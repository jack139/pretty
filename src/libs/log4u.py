#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time, hashlib
import traceback 
import json, urllib3, urllib
from bson.objectid import ObjectId
from config import setting
import app_helper

db = setting.db_web

# 记录操作日志

# 日志事件类型
DUE             = 10 # 已下单、待支付
TIMEOUT         = 20 # 付款超时，取消订单
USER_CANCEL_DUE = 30 # 用户：未付款、取消订单
SYS_CANCEL_DUE  = 40 # 系统：未付款、取消订单
PAID_AND_WAIT   = 50 # 拼团订单：已支付待成团
PREPAID         = 60 # 付款确认中
PT_SUCC         = 70 # 拼团订单：拼团成功
PAID            = 80 # 付款成功（非拼团订单）
REDUCE_STOCK    = 85 # 扣减库成功存(1小时,次日达仓库订单)
USER_CONFIRM    = 230 # 用户：确认收货
SYS_CANCEL_ORDER= 250 # 系统：取消订单（余额不足、抽奖失败、刷单订单、不在配送范围）
PT_FAIL         = 260 # 拼团失败
REFUND          = 280 # 财务：提交退款成功（订单已取消）
APP_CANCEL_ORDER= 270 # APP取消已支付的订单
OTHERS          = 100000 # 其他


# 推送订单到backrun 队列
def log_push(log_id):
    db.event_queue.insert_one({
        'type' : 'PUSH_LOG',
        'status' : 'WAIT',
        'data' : {
            'log_id' : log_id,
        }
    })

def log(act_user, log_event, log_message, order_id=None, log_json={}, send_to_log_server=1):
    # 访问记录
    env_info = web.ctx.get('environ')
    if env_info:
        request_info = {
            'remote_addr' : env_info.get('REMOTE_ADDR'),
            'remote_port' : env_info.get('REMOTE_PORT'),
            'request_method' : env_info.get('REQUEST_METHOD'),
            'request_uri' : env_info.get('REQUEST_URI'),
            'user_agent'  : env_info.get('HTTP_USER_AGENT'),
        }
    else:
        request_info = {}

    # order_id 填在log_json里
    if order_id:
        log_json['order_id']=order_id

    r=db.action_log.insert_one({
        'log_time'     : app_helper.time_str(),
        'act_user'     : act_user,
        'log_event'    : log_event,
        'log_message'  : log_message,
        'log_json'     : log_json, # None 或 json 数据
        'request_info' : request_info,
        'send_to_log_server' : send_to_log_server, # 1 发送 0 不发送
    })

    #发到日志中心的log
    if send_to_log_server:
        log_push(r.inserted_id)

    return r.inserted_id

def log_sent(log_id):
    return db.action_log.update_one({'_id':ObjectId(log_id)}, {'$set':{'sent_time':app_helper.time_str()}})


############==== 日志中心接口 ============================================

if app_helper.IS_TEST or app_helper.IS_STAGING:
    SERV_HOST = '120.26.210.28'
    SERV_PORT = 10070
else:
    SERV_HOST = '10.27.227.76'
    SERV_PORT = 10070
'''

SERV_HOST = 'ordermonitor-dev.urfresh.cn' #'192.168.1.186'
SERV_PORT = 80
'''

def send_request(method, url, body=None):
    try:
        conn = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
        if method=='POST':
            header = {'Content-Type': 'application/json'}
        else:
            header = None
        url2 = 'http://%s:%s/%s' % (SERV_HOST, SERV_PORT, url)
        print url2
        #print header
        print body
        r = conn.urlopen(method, url2, body=body, headers=header)
        
        print r.status
        print r.data

        r0 = r.data
        r1 = json.loads(r0)
        return r1
    except Exception, e:
        print method, url
        traceback.print_exc()
        return False


def oms_log(order_id, chg_id, chg_type, chg_time, des, content, ip):
    req = {
        "orderCode" : order_id,
        "chgId"     : chg_id,
        "chgType"   : chg_type, 
        "chgTime"   : chg_time, 
        "des"       : des, 
        "content"   : content, 
        "source"    : 'front', 
        "ip"        : ip, 
    }

    r = send_request('POST', 'log', json.dumps(req))

    if r and r['code']==0:
        return True
    else:
        return False


def oms_get_log(order_id):

    r = send_request('GET', 'log/%s'%order_id)

    if r and r['code']==0:
        return r['data']
    else:
        return False


# 推送一条action_log里的日志, backrun 推送使用
def push_log_to_oms(log_id):
    if not isinstance(log_id, ObjectId):
        log_id = ObjectId(log_id)

    # 使用primary获取数据，防止mongo数据同步问题
    r = setting.db_primary.action_log.find_one({'_id':log_id})
    if not r:
        return 'DONE', '日志不存在'

    oms_log(
        r['log_json'].get('order_id','na'),
        str(r['_id']),
        r['log_event'],
        r['log_time'],
        r['log_message'],
        json.dumps(r['log_json']),
        r['request_info'].get('remote_addr','')
    )

    status = 'DONE'
    msg = '已推送日志'

    print msg, str(log_id)
    return status, msg

# 记录接口日志
def interface_log(url, param, result):
    r=db.interface_log.insert_one({
        'log_time' : app_helper.time_str(),
        'url'      : url,
        'param'    : param,
        'result'   : result,
    })
