#!/usr/bin/env python
# -*- coding: utf-8 -*-
#

# 前端代码 公用变量及函数

import time, os, hashlib
import urllib, urllib3, json
import functools
import re
import web
from config import setting

#---------------------------- 标记是否在测试／staging环境，用于区别生成环境的一些设置
IS_TEST = 'dev' in setting.app_host
IS_STAGING = 'dev' in setting.app_host
#----------------------------

if IS_TEST:
    from app_settings_test import * 
elif IS_STAGING:
    from app_settings_stag import * 
else:
    from app_settings import * 

db = setting.db_web

# 时间函数
ISOTIMEFORMAT=['%Y-%m-%d %X', '%Y-%m-%d', '%Y%m%d%H%M', '%Y-%m-%d %H:%M']

def time_str(t=None, format=0):
    return time.strftime(ISOTIMEFORMAT[format], time.localtime(t))

def validateEmail(email):
    if len(email) > 7:
      if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", email) != None:
          return 1
    return 0

RAND_BASE=[
    'abcdefghijklmnopqrstuvwxyz',
    '0123456789',
]

def my_rand(n=4, base=0):
    import random
    return ''.join([random.choice(RAND_BASE[base]) for ch in range(n)])


# 内部使用号码，固定验证码, 2015-12-22, gt
INNER_NUM = {
    '18516569412' : '9998',
}



#==========================================================================


BLOCK_LIST = [
    '15000623214',
    #'13194084665',
]



# 查询session
def get_session(session_id):
    return db.app_sessions.find_one_and_update({'session_id':session_id},{'$set':{'attime':time.time()}})

# 检查session登录状态
def logged(session_id):
    session = get_session(session_id)
    if session==None:
        return None
    else:
        #db.app_user.update_one({'uname' : session['uname']},{
        #   '$set'  : {'last_time' : time_str()}
        #})
        if session['login']==1: # 登录后返回uname
            return session['uname']
        else:
            return None

# 检查session登录状态, 合并app与微信订单
def app_logged(session_id):
    session = get_session(session_id)
    if session==None:
        return None
    else:
        #db.app_user.update_one({'uname' : session['uname']},{
        #   '$set'  : {'last_time' : time_str()}
        #})
        if session['login']==1: # 登录后返回uname,openid
            return {'uname' : session['uname'], 'openid': session.get('openid',''),  'unionid': session.get('unionid',''),
                    'type': session.get('type','app')}
        else:
            return None

# 检查openid
def check_openid(openid):
    #r = db.app_user.find_one_and_update(
    #    {'openid' : openid},
    #    {'$set'   : {'last_time' : time_str()}},
    #    {'uname' : 1, 'openid':1}
    #)
    #if r:
    #    return {'uname' : r.get('uname',''), 'openid': r['openid']}
    #else:
        return None

# 微信检查session登录状态
def wx_logged(session_id):
    session = get_session(session_id)
    if session==None:
        return None
    else:
        #db.app_user.update_one({'uname' : session['uname']},{
        #   '$set'  : {'last_time' : time_str()}
        #})
        if session['login']==1: # 登录后返回uname
            #return session['uname']
            return {'uname' : session['uname'], 'openid': session['openid'], 'unionid': session.get('unionid','')}
        else:
            return None

def generate_sign(c): # c时列表，c[0]一定是app_id
    db_dev = db.app_device.find_one({'app_id' : c[0]}, {'private_key':1})
    if db_dev==None:
        return None
        #return json.dumps({'ret' : -3, 'msg' : 'app_id错误'})
    else:
        #验证签名
        sign_str = '%s%s' % (db_dev['private_key'], ''.join(i for i in c))
        print sign_str
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()




# 生成order_id
def get_new_order_id(version='v1', prefix='acme'):
    if IS_TEST or IS_STAGING:
        surfix = '-test'
    else:
        surfix = ''

    cc=1
    while cc!=None:
        # order_id 城市(1位)+日期时间(6+4位)+随机数(5位)+版本
        order_id = '%s20%s%s%s%s' % (prefix,time_str(format=2)[2:],my_rand(6,1),version[-1],surfix)
        cc = db.order_app.find_one({'order_id' : order_id},{'_id':1})
    db.order_app.insert_one({'order_id':order_id}) # 先占位 2016-03-17,gt
    return order_id

# 取得设备类型
def get_devive_type(app_id):
    db_dev = db.app_device.find_one({'app_id':app_id},{'type':1})
    if db_dev:
        return db_dev['type']
    else:
        return ''


# 获取access_token，与wx.py 中相同
def get_token(force=False, region_id=None): # force==True 强制刷新
    if region_id==None:
        region_id = setting.region_id
    print 'region: ', region_id
    if not force:
        db_ticket = db.jsapi_ticket.find_one({'region_id':region_id})
        if db_ticket and int(time.time())-db_ticket.get('token_tick', 0)<3600:
            if db_ticket.get('access_token', '')!='':
                print db_ticket['access_token']
                return db_ticket['access_token']

    url='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
        (setting.WX_store[region_id]['wx_appid'], setting.WX_store[region_id]['wx_appsecret'])
    f=urllib.urlopen(url)
    data = f.read()
    f.close()

    t=json.loads(data)
    if t.has_key('access_token'):
        print t
        db.jsapi_ticket.update_one({'region_id':region_id},
            {'$set':{'token_tick':int(time.time()), 'access_token':t['access_token']}},upsert=True)
        return t['access_token']
    else:
        db.jsapi_ticket.update_one({'region_id':region_id},
            {'$set':{'token_tick':int(time.time()), 'access_token':''}},upsert=True)
        return ''

def wx_reply_msg0(openid, text, force=False, region_id=None):
    text0 = text.encode('utf-8') if type(text)==type(u'') else text
    body_data = '{"touser":"%s","msgtype":"text","text":{"content":"%s"}}' % (str(openid), text0)
    urllib3.disable_warnings()
    http = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
    url = 'https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token=%s'%get_token(force, region_id)
    try:
        r = http.request('POST', url,
            headers={'Content-Type': 'application/json'},
            body=body_data)
        if r.status==200:
            return json.loads(r.data)
        else:
            print 'http fail: ', r.status
            return None
    except Exception,e:
        print '%s: %s (%s)' % (type(e), e, url)
        return None


def wx_reply_msg(openid, text, region_id=None):
    print 'openid: ', openid
    if region_id.strip()=='':
        print 'region_id is BLANK'
        return None
    r = wx_reply_msg0(openid, text, region_id=region_id)
    if r==None or r.get('errcode', 0)!=0:
        # 发送失败，强制刷新token后再发一次
        print r
        r = wx_reply_msg0(openid, text, force=True, region_id=region_id)
    return r

# 后台发送微信推送信息
def event_send_wx_msg(openid, text, region_id, url=''):
    db.event_queue.insert_one({
        'type' : 'WX_MSG',
        'status' : 'WAIT',
        'data' : {
            'region_id' : region_id,
            'openid'    : openid,
            'text'      : text,
            'url'       : url
        }
    })

# 推送订单到WMS
def event_push_order(order_id):
    if order_id.strip()=='':
        return None
    db.event_queue.insert_one({
        'type' : 'PUSH_ORDER',
        'status' : 'WAIT',
        'data' : {
            'order_id' : order_id,
        }
    })


"""
    用于请求签名验证的修饰器

    @param sign_names 需要参与签名的参数名列表
        需要按顺序, sign_names[0]为app_id
    @param param_defaults 非必须的参数
"""
def check_sign(param_names):
    def _wrap(func):
        @functools.wraps(func)
        def __wrap(*args, **kw):
            # 获取参数, 缺少必须参数返回错误
            defaults = dict((el,'') for el in param_names)
            try:
                param = web.input('app_id', 'dev_id', 'ver_code', 'tick', 'sign', **defaults)
            except:
                print web.input()
                return api_error(-2, '缺少参数')

            print param

            # 验证签名,验证失败返回错误
            sign_data = [param[name] for name in param_names]
            #print sign_data
            md5_str = generate_sign(sign_data)
            if md5_str != param.sign:
                print '------> 签名验证错误 in check_sign'
                print md5_str, param.sign
                return api_error(-1, '签名验证错误')

            return func(*args, **kw)
        return __wrap
    return _wrap


# 用于返回api 错误信息 
def api_error(ret, msg=''):
    # 防止web.py的影响
    web.ctx.status = '200 OK'
    web.ctx.headers = [('Content-Type', 'application/json')]

    return json.dumps({'ret': ret, 'msg': msg})
