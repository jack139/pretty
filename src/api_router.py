#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os, gc
from pymongo import MongoClient
import time, json, hashlib, random
import rsa, base64
import traceback 
from bson.objectid import ObjectId
from config import setting
import app_helper 
from libs import pt_succ
from libs import settings_helper
from libs import credit_helper
from libs import app_user_helper
from libs import log4u
from libs.cancel_dsv import cancel_dsv_order

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


db = setting.db_primary  # 默认db使用web本地

urls = [
    '/app/v1/first_hand',  'FisrtHand_v2',
    '/app/v1/get_host',    'GetHost',
    '/app/v1/alipay_notify',   'AlipayNotify',
    '/app/v1/wxpay_notify',    'WxpayNotify',
]

app = web.application(urls, globals())
application = app.wsgifunc()

#----------------------------------------

gc.set_threshold(300,5,5)

###########################################

def my_crypt(codestr):
    return hashlib.sha1("sAlT139-"+codestr).hexdigest()

def my_rand(n=8):
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for ch in range(n)])

########### APP接口 #######################################################

## 需优化内容：
# 1. 出错info页面要做微信端优化 --> 直接跳转回init页面
# 2. urlopen, json.loads 需要处理异常！


# 常量
public_key='DDACE9D14B3413C65991278F09A03896'
public_key_v2='DHTTG9D14B3413C65991278F09A03896'


##### 核对签名  =======================================================

def quick(L):
    if len(L) <= 1: return L
    return quick([a for a in L[1:] if a[0] < L[0][0]]) + L[0:1] + quick([b for b in L[1:] if b[0] >= L[0][0]])

def check_sign_wx(str_xml):
    api_key='0378881f16430cf597cc1617be53db37'

    xml=ET.fromstring(str_xml)
    params = []
    sign0 = None
    for i in xml:
        if i.tag=='sign':
            sign0 = i.text
            continue
        params.append((i.tag, i.text))

    param2 = quick(params)
    stringA = '&'.join('%s=%s' % (i[0],i[1]) for i in param2)
    stringSignTemp = '%s&key=%s' % (stringA, api_key)
    sign = hashlib.md5(stringSignTemp).hexdigest().upper()
    return (sign0==sign)

RSA_PUBLIC = "-----BEGIN PUBLIC KEY-----\n" \
    "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCnxj/9qwVfgoUh/y2W89L6BkRA\n" \
    "FljhNhgPdyPuBV64bfQNN1PjbCzkIM6qRdKBoLPXmKKMiFYnkd6rAoprih3/PrQE\n" \
    "B/VsW8OoM8fxn67UDYuyBTqA23MML9q1+ilIZwBC2AQ2UBVOrFXfFl75p6/B5Ksi\n" \
    "NG9zpgmLCUYuLkxpLQIDAQAB\n" \
    "-----END PUBLIC KEY-----"

def check_sign_alipay(ret):
    params = []
    sign0 = None
    for i in ret.keys():
        if i=='sign_type':
            continue
        elif i=='sign':
            sign0 = ret[i]
            continue
        params.append((i, ret[i]))

    param2 = quick(params)
    stringA = '&'.join('%s=%s' % (i[0],i[1]) for i in param2)
    _public_rsa_key_ali = rsa.PublicKey.load_pkcs1_openssl_pem(RSA_PUBLIC)
    sign = base64.decodestring(sign0)
    try:
        rsa.verify(stringA.encode('utf-8'), sign, _public_rsa_key_ali)
        return True
    except Exception,e:
        print "check_sign_alipay error: ", e
        return False

##### ==================================================================

# 首次握手 v2，公钥不同
class FisrtHand_v2:
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param=web.input(type='', secret='', sign='')

        print web.data()

        if '' in (param.type, param.secret, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.type not in ['IOS', 'ANDROID']:
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        sign_str = '%s%s%s' % (public_key_v2, param.type, param.secret)
        md5_str = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        # 注册新app
        app_id = my_rand().upper()
        if db.app_device.find({'app_id' : app_id}).count()>0:
            # 两次随机仍重复的可能性，很小吧
            app_id = my_rand().upper()
        private_key = my_crypt(app_id).upper()
        db.app_device.insert_one({
            'app_id'      : app_id, 
            'private_key' : private_key, 
            'type'        : param.type
        })

        return json.dumps({'ret' : 0, 'data' : {
            'app_id'      : app_id,
            'private_key' : private_key,
        }})

# 灰度测试的app_id
GREY_TEST = [
    #'TVQ2P8V7', # 13194084665
    #'1NHX2NOM', # 13917689006
    #'3JF9EMH8', # 13167202832
    #'TDLEP5BD', # 13185333855
    #'Y19GD0S0', # 13651794606
    #'IHG16V7N', # o8wS2t8jZEXV3bF5lzKqtDjVrW6Y
]
# 取得主机端口
class GetHost:
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', secret='', sign='')

        if '' in (param.app_id, param.secret, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.secret])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        # 返回host地址、端口
        if param.app_id in GREY_TEST:
            host = 'app0.urfresh.cn'
        else:
            host = setting.app_pool[random.randint(0,len(setting.app_pool)-1)]
        print 'host = ', host
        return json.dumps({'ret' : 0, 'data' : {
            'protocol' : 'http',
            #'host'     : setting.app_host, #'app.urfresh.cn',
            'host'     : host,
            'port'     : '12050',
            'https_port' : '12051',
        }})

# 阿里云异步通知
# { 'seller_email': u'pay@urfresh.cn', 
#   'refund_status': u'REFUND_SUCCESS', 
#   'trade_status': u'TRADE_CLOSED', 
#   'gmt_close': u'2015-07-26 22:10:10', 
#   'sign': u'GuNPbLf5+qEtGbcgroLtbocHEuA7srFhj12lBCTg2ZC/mbi08GtcB0loQx5K4DS2KLbKhkBOtQZf4u1Nhln9G03SjBpQZwz11xyQNXjBvKNkk3jfiE6T5KGtWpp8Y4sCQXySoYjh6M70JKajyHwupxGvBxcxcRPSRUp14J2SXP8=', 
#   'gmt_refund': u'2015-07-26 22:10:10', 'subject': u'U\u638c\u67dc', 'is_total_fee_adjust': u'N', 
#   'gmt_create': u'2015-07-26 21:55:41', 'out_trade_no': u'n000148', 'sign_type': u'RSA', 
#   'body': u'n000148', 'price': u'1.00', 'buyer_email': u'1010694499@qq.com', 'discount': u'0.00', 
#   'gmt_payment': u'2015-07-26 21:55:42', 
#   'trade_no': u'2015072600001000290059171016', 'seller_id': u'2088021137384128', 
#   'use_coupon': u'N', 'payment_type': u'1', 'total_fee': u'1.00', 'notify_time': u'2015-07-26 22:10:11', 
#   'quantity': u'1', 'notify_id': u'45a440807ef37f807132a25e8445844d3m', 
#   'notify_type': u'trade_status_sync', 'buyer_id': u'2088502264376292'    }
class AlipayNotify:
    def POST(self, version='v1'):
        param = web.input()
        print param

        if check_sign_alipay(param):
            print "ALIPAY SIGNATURE CHECK SUCCESS!"
        else:
            print "ALIPAY SIGNATURE CHECK FAIL ......!"
            return 'fail'
        #print "=================="
        order_id = param.get('out_trade_no','')

        if order_id[0]=='d': # 充值订单
            print '充值订单'
            if param.get('trade_status') == 'TRADE_SUCCESS' and (not param.has_key('refund_status')):
                print '充值操作'
                #订单是否重复充值
                r = db.deposit_order.find_one_and_update(
                    {'$and': [
                            {'deposit_order_id' : order_id},
                            {'pay_flag' : {'$ne':1}},
                        ]
                    },
                    {'$set': {'pay_flag':1}}, # 用于多线程互斥
                )
                print 'test$$$$$$$$$$$$$'
                print r
                if not r:
                    return 'success' # 这里就返回啦
                alipay_total = param.get('total_fee','0.00') # 支付宝实际支付
                ali_trade_no = param.get('trade_no')
                ret = credit_helper.deposit_to_credit_balance(order_id, 'ALIPAY', 
                    alipay_total, ali_trade_no, param)
                print 'ret= %r'%ret
            else:
                print '不是付款成功通知'
            return 'success' # 这里就返回啦

        if param.get('refund_status') == 'REFUND_SUCCESS' and param.get('trade_status') != 'TRADE_FINISHED': # 有退款
            rr = db.oms_refund_log.find_one_and_update({'order_id': order_id, 'refund_status': 'REFUND_ING'},
                                                       {'$set': {'refund_time': app_helper.time_str(), 'refund_status':
                                                       'REFUND', 'last_status': int(time.time())},
                                                       '$push': {'history': (app_helper.time_str(), 'page', '退款通知')}},
                                                        {'refund_code': 1, 'app_flag': 1})
            if rr:
                # 退款货不需要更新退款状态，是否更新根据黄凯传过来的标识
                if int(rr['app_flag']) in [1, 2]:
                    r = db.order_app.update_one({'order_id': order_id}, {
                        '$set'  : {
                            'status'      : 'REFUND',
                            'REFUND'      : int(time.time()), # 2016-01-10, gt
                            'last_status' : int(time.time()),
                        },
                        '$push' : {
                            'ali_notify': param,
                            'history'   : (app_helper.time_str(), 'alipy', '已操作退款')
                        }
                    })
                # 订单推MQ --- 在 update_product_refund 里 推，这里不推了
                #app_helper.event_push_mq(order_id, 'REFUND')
                from refund_helper import push_mq
                push_mq(order_id, rr['refund_code'])
                # 推送订单
                if int(rr['app_flag']) in [1, 2]:
                    try:
                        data = cancel_dsv_order(str(order_id.encode('utf-8')), 'REFUND')
                        print "<%s>>>>>(退款)推送订单%s>>>%s" % (app_helper.time_str(), str(order_id.encode('utf-8')), data)
                    except Exception, e:
                        print "<%s>>>>>(退款)推送订单%s失败>>>%s" % (app_helper.time_str(), str(order_id.encode('utf-8')), str(e))
                        traceback.print_exc()

        elif param.get('trade_status') == 'TRADE_SUCCESS': # 有付款
            r = db.order_app.find_one({'order_id':order_id},
                #{'due':1, 'uname':1, 'coupon':1, 'shop':1, 'cart':1, 'status':1})
                {'_id':0})
            if r:
                status = r['status'] #'PAID' 保持状态

                comment = '' # 用于记录history时附加信息 2015-11-21

                due_amount = float(r.get('due3',r['due']))
                recv_amount = float(param.get('total_fee','0'))
                print '收到金额：',due_amount,recv_amount,due_amount-recv_amount
                if due_amount-recv_amount>0.10: # 检查支付金额与应付是否一致
                    print '部分付款！'

                    status = 'PARTIAL_PAID'
                    db.order_app.update_one({'order_id': order_id}, {
                        '$set'  : {
                            'status'      : status,
                            status      : int(time.time()), # 2016-01-10, gt
                            'last_status' : int(time.time()), 
                        },
                        '$push' : {
                            'ali_notify': param,
                            'history'   : (app_helper.time_str(), 'alipy', '部分收款')
                        }
                    })

                    return 'success' # 这里就返回啦


                print r['status']

                #db_user = db.app_user .find_one({'$or' : [ 
                #    {'uname':r['uname']},{'openid':r['uname']}  # 2015-08-22
                #]})
                db_user = app_user_helper.get_user_info(r['uname'], q_type='both')

                transaction_id = param.get('trade_no')
                if r['status'] in ['DUE', 'PREPAID', 'TIMEOUT'] and \
                    r.get('ali_trade_no')!=transaction_id: # 如果状态已是PAID，说明有重复通知，不减库存
                    # 默认这时候可以为PAID了，但也不一定
                    status = 'PAID'

                    # 消费余额
                    if float(r.get('use_credit', '0'))>0:
                        used_balance = credit_helper.consume_balance(
                            r['uname'], 
                            float(r['use_credit']),
                            '订单: %s' % order_id.encode('utf-8'),
                            order_id=order_id
                        )
                        if used_balance==False: # 余额不够用

                            # 修改订单状态
                            db.order_app.update_one({'order_id':order_id},{
                                '$set'  : {
                                    'status'       : 'CANCEL_TO_REFUND',
                                    #'sum_to_refund' : r['due'], # 没有 sum_to_refund 表示全额退
                                    'use_credit'    : '0.00', # 清除余额支付，防止多退款
                                    'use_credit_old': r['use_credit'], # 保存应收余额支付金额
                                    #'cart'         : b2,     # 更新购物车  2015-09-11
                                    'ali_trade_no' : transaction_id,
                                    'paid_time'    : param.get('gmt_payment'),
                                    'paid_tick'    : int(time.time()),
                                    'pay_type'     : 'ALIPAY_CREDIT',
                                    'CANCEL_TO_REFUND' : int(time.time()), # 2016-01-10, gt
                                    'last_status' : int(time.time()), 
                                },
                                '$push' : {
                                    'ali_notify': param,
                                    'history'   : (app_helper.time_str(), 'alipay', '付款通知:余额不足转入退款')
                                }
                            })
                            # 订单推MQ
                            app_helper.event_push_mq(order_id, 'CANCEL_TO_REFUND')
                            log4u.log('AlipayNotify', log4u.SYS_CANCEL_ORDER , '余额不足转入退款', order_id)

                            return 'success'

                    # 邀请码用户送抵用券 2015-10-24
                    #invitation = db_user.get('invitation', '')
                    #if invitation!='' and db_user.get('invite_coupon_has_sent', 0)==0: # 已填邀请码并且未送过券
                    #    #coupon_user = db.app_user .find_one({'my_invit_code':invitation},{'uname':1})
                    #    coupon_user = app_user_helper.get_user_by_invit_code(invitation)
                    #    if coupon_user:
                    #        # 送邀请码用户抵用券
                    #        # 使用新抵用券 2016-02-29, gt
                    #        print '送邀请码用户抵用券'
                    #        try:
                    #            settings_helper.give_coupon_to_user(
                    #                coupon_active_code = app_helper.COUPON_SET['INVIT_ORDER'],
                    #                uname=coupon_user['uname'],
                    #                unionid=coupon_user.get('unionid','')
                    #            )
                    #        except Exception, e:
                    #            print 'Error', e
                    #            traceback.print_exc()
                    #            pass

                    #        # 设置已送标志
                    #        db.app_user.update_one({'uname':r['uname']}, {'$set':{
                    #            'invite_coupon_has_sent' : 1,
                    #            'last_status'            : int(time.time()),
                    #        }})

                    b2 = r['cart']
                    b2s = [] # 除 mall 订单外，其他订单 cart_list为空

                    if r['type'] in ['TUAN', 'SINGLE']: #order_id[0]=='t': # 拼团订单处理
                        # 不修改购物车内容
                        status, comment = pt_succ.process_tuan_after_paid(r, 'alipay')

                    elif r['type'] == 'MALL': # 商家订单
                        b2s = pt_succ.process_mall_after_paid(r, 'alipay')

                    else: # 普通1小时订单: n开头、e开头
                        b2 = pt_succ.process_1hour_after_paid(r, 'alipay', status)

                    # 推送通知
                    #if len(r['uname'])==11 and r['uname'][0]=='1':
                    #   jpush.jpush('已收到您的付款，我们会尽快处理。', r['uname'])

                    # 有些状态修改会比较快，避免异步操作造成的状态错误
                    r8 = db.order_app.find_one_and_update(
                        {
                            'order_id' : order_id,
                            'status' : {'$in':['DUE', 'PREPAID', 'TIMEOUT']},
                        },
                        {
                            '$set' : {
                                'status' : status,
                                status   : int(time.time()),
                            },
                        },
                        {'order_id':1}
                    )
                    if r8==None:
                        print '订单状态已改变，未修改:', status, order_id.encode('utf-8')
                    else:
                        print '订单状态修改:', status, order_id.encode('utf-8')
                else:
                    print "重复通知：alipay"
                    b2 = r['cart']
                    b2s = []
                    used_balance = {
                        'credit' : float(r.get('credit_cash_used',0)),
                        'return_cash' : float(r.get('return_cash_used',0)),
                    }


                # 修改订单状态
                db.order_app.update_one({'order_id':order_id},{
                    '$set'  : {
                        #'status'       : status,
                        'cart'         : b2,     # 更新购物车  2015-09-11
                        'cart_list'    : b2s,    # 只有mall订单有数据
                        'ali_trade_no' : transaction_id,
                        'paid_time'    : param.get('gmt_payment'),
                        'paid_tick'    : int(time.time()),
                        'pay_type'     : 'ALIPAY_CREDIT' if float(r.get('use_credit', '0'))>0 else 'ALIPAY',
                        'credit_total' : '%.2f' % float(r.get('use_credit', '0')),
                        'credit_cash_used' : '%.2f'%used_balance['credit'] if float(r.get('use_credit', '0'))>0 else '0.00',
                        'return_cash_used' : '%.2f'%used_balance['return_cash'] if float(r.get('use_credit', '0'))>0 else '0.00',
                        'alipay_total' : param.get('total_fee','0.00'), # 支付宝实际支付
                        #status        : int(time.time()), # 2016-01-10, gt
                        'last_status' : int(time.time()), 
                    },
                    '$push' : {
                        'ali_notify': param,
                        'history'   : (app_helper.time_str(), 'alipay', '已付款'+comment)
                    }
                })

                # 更新app_order_num 20160927 lf
                if status in ['PAID', 'PAID_AND_WAIT']:
                    if len(db_user.get('uname', '')) == 11:  # 手机号码下单
                        db.app_user.update_one({'uname': db_user['uname']}, {'$set': {'app_order_num': 1}})
                    elif len(db_user.get('openid', '')) > 11:  # openid下单
                        db.app_user.update_one({'openid': db_user['openid']}, {'$set': {'app_order_num': 1}})

                # 推 MQ
                if r['type'] in ['TUAN', 'SINGLE']:
                    if status == 'PAID':
                        app_helper.event_push_mq(order_id,'PAID')
                        app_helper.event_push_mq(order_id,'PT_SUCC')
                        log4u.log('AlipayNotify', log4u.PAID , '付款成功', order_id)
                        #log4u.log('AlipayNotify', log4u.PT_SUCC , '拼团成功', order_id)
                    elif status == 'PAID_AND_WAIT':
                        app_helper.event_push_mq(order_id,'PAID')
                        log4u.log('AlipayNotify', log4u.PAID_AND_WAIT , '付款成功，待成团', order_id)
                    elif status == 'FAIL_TO_REFUND':
                        app_helper.event_push_mq(order_id,'PAID')  # 拼团失败也要推支付信息 2016-09-21
                        app_helper.event_push_mq(order_id,'CANCEL_TO_REFUND')
                        log4u.log('AlipayNotify', log4u.PAID , '付款成功', order_id)
                        log4u.log('AlipayNotify', log4u.SYS_CANCEL_ORDER , '订单取消', order_id)
                    else:
                        print '不该出现的状态', str(status)
                else:
                    if status == 'PAID':
                        app_helper.event_push_mq(order_id,'PAID')
                        log4u.log('AlipayNotify', log4u.PAID , '付款成功', order_id)
                    else:
                        print '不该出现的状态', str(status)

        return 'success'


# 微信支付异步通知
#<xml>
#  <appid><![CDATA[wx2421b1c4370ec43b]]></appid>
#  <attach><![CDATA[支付测试]]></attach>
#  <bank_type><![CDATA[CFT]]></bank_type>
#  <fee_type><![CDATA[CNY]]></fee_type>
#  <is_subscribe><![CDATA[Y]]></is_subscribe>
#  <mch_id><![CDATA[10000100]]></mch_id>
#  <nonce_str><![CDATA[5d2b6c2a8db53831f7eda20af46e531c]]></nonce_str>
#  <openid><![CDATA[oUpF8uMEb4qRXf22hE3X68TekukE]]></openid>
#  <out_trade_no><![CDATA[1409811653]]></out_trade_no>
#  <result_code><![CDATA[SUCCESS]]></result_code>
#  <return_code><![CDATA[SUCCESS]]></return_code>
#  <sign><![CDATA[B552ED6B279343CB493C5DD0D78AB241]]></sign>
#  <sub_mch_id><![CDATA[10000100]]></sub_mch_id>
#  <time_end><![CDATA[20140903131540]]></time_end>
#  <total_fee>1</total_fee>
#  <trade_type><![CDATA[JSAPI]]></trade_type>
#  <transaction_id><![CDATA[1004400740201409030005092168]]></transaction_id>
#</xml>
class WxpayNotify:
    def POST(self, version='v1'):
        param = web.input()
        print param

        str_xml=web.data()
        print str_xml

        if check_sign_wx(str_xml):
            print "WXPAY SIGNATURE CHECK SUCCESS!"
        else:
            print "WXPAY SIGNATURE CHECK FAIL ......!"
            return  '<xml>' \
                '<return_code><![CDATA[FAIL]]></return_code>' \
                '<return_msg><![CDATA[签名失败]]></return_msg>' \
                '</xml>' 

        xml=ET.fromstring(str_xml)
        return_code = xml.find('return_code').text
        if return_code!='SUCCESS':  # 通信失败
            return  '<xml>' \
                '<return_code><![CDATA[FAIL]]></return_code>' \
                '<return_msg><![CDATA[FAIL]]></return_msg>' \
                '</xml>' 

        result_code = xml.find('result_code').text
        if result_code=='SUCCESS': # 有付款
            # v2 开始微信支付out_trade_no，在order_id后加时间戳 2015-09-19
            order_id0 = xml.find('out_trade_no').text
            order_id = order_id0.split('_')[0]

            if order_id[0]=='d': # 充值订单
                print '充值订单'
                print '充值操作'
                #订单是否重复充值
                r = db.deposit_order.find_one_and_update(
                    {'$and': [
                            {'deposit_order_id' : order_id},
                            {'pay_flag' : {'$ne':1}},
                        ]
                    },
                    {'$set': {'pay_flag':1}}, # 用于多线程互斥
                )
                print 'test$$$$$$$$$$$$$'
                print r
                if not r:
                    return  '<xml>' \
                        '<return_code><![CDATA[SUCCESS]]></return_code>' \
                        '<return_msg><![CDATA[OK]]></return_msg>' \
                        '</xml>' 
                
                wxpay_total = xml.find('total_fee').text # 微信支付实际支付，单位：分
                wx_trade_no = xml.find('transaction_id').text
                ret = credit_helper.deposit_to_credit_balance(order_id, 'WXPAY', 
                    wxpay_total, wx_trade_no, str_xml)
                print 'ret= %r'%ret

                return  '<xml>' \
                    '<return_code><![CDATA[SUCCESS]]></return_code>' \
                    '<return_msg><![CDATA[OK]]></return_msg>' \
                    '</xml>' 

            r = db.order_app.find_one({'order_id':order_id},
                #{'due':1, 'uname':1, 'coupon':1, 'shop':1, 'cart':1, 'status':1})
                {'_id':0})
            if r:
                status = r['status'] #'PAID' 保持状态

                comment = '' # 用于记录history时附加信息 2015-11-21

                due_amount = int(float(r.get('due3',r['due']))*100)
                recv_amount = int(xml.find('total_fee').text)
                print '收到金额：',due_amount,recv_amount,due_amount-recv_amount
                if due_amount-recv_amount>10: # 检查支付金额与应付是否一致
                    print '部分付款！'

                    status = 'PARTIAL_PAID'
                    db.order_app.update_one({'order_id': order_id}, {
                        '$set'  : {
                            'status'      : status,
                            status      : int(time.time()), # 2016-01-10, gt
                            'last_status' : int(time.time()), 
                        },
                        '$push' : {
                            'wx_notify' : str_xml,
                            'history'   : (app_helper.time_str(), 'wxpay', '部分收款')
                        }
                    })

                    return  '<xml>' \
                        '<return_code><![CDATA[SUCCESS]]></return_code>' \
                        '<return_msg><![CDATA[OK]]></return_msg>' \
                        '</xml>' 


                print r['status']

                #db_user = db.app_user .find_one({'$or' : [ 
                #    {'uname':r['uname']},{'openid':r['uname']}  # 2015-08-22
                #]})
                db_user = app_user_helper.get_user_info(r['uname'], q_type='both')

                transaction_id = xml.find('transaction_id').text

                if r['status'] in ['DUE', 'PREPAID', 'TIMEOUT'] and \
                    r.get('wx_trade_no')!=transaction_id: # 如果状态已是PAID，说明有重复通知，不减库存
                    # 默认这时候可以为PAID
                    status = 'PAID'

                    # 消费余额
                    if float(r.get('use_credit', '0'))>0:
                        used_balance = credit_helper.consume_balance(
                            r['uname'], 
                            float(r['use_credit']),
                            '订单: %s' % order_id.encode('utf-8'),
                            order_id=order_id
                        )
                        if used_balance==False: # 余额不够用

                            # 修改订单状态
                            t = xml.find('time_end').text
                            paid_time = '%s-%s-%s %s:%s:%s' % (t[:4],t[4:6],t[6:8],t[8:10],t[10:12],t[12:])
                            db.order_app.update_one({'order_id':order_id},{
                                '$set'  : {
                                    'status'       : 'CANCEL_TO_REFUND',
                                    #'sum_to_refund' : r['due'],
                                    'use_credit'    : '0.00', # 清除余额支付，防止多退款
                                    'use_credit_old': r['use_credit'], # 保存应收余额支付金额
                                    #'cart'         : b2,     # 更新购物车  2015-09-11
                                    'wx_trade_no'  : transaction_id,
                                    'paid_time'    : paid_time,
                                    'paid_tick'    : int(time.time()),
                                    'wx_out_trade_no'  : order_id0,
                                    'pay_type'     : 'WXPAY_CREDIT',
                                    'CANCEL_TO_REFUND' : int(time.time()), # 2016-01-10, gt
                                    'last_status' : int(time.time()), 
                                },
                                '$push' : {
                                    'wx_notify' : str_xml,
                                    'history'   : (app_helper.time_str(), 'wxpay', '付款通知:余额不足转入退款')
                                }
                            })
                            # 订单推MQ
                            app_helper.event_push_mq(order_id, 'CANCEL_TO_REFUND')
                            log4u.log('WxpayNotify', log4u.SYS_CANCEL_ORDER , '余额不足转入退款', order_id)

                            return  '<xml>' \
                                '<return_code><![CDATA[SUCCESS]]></return_code>' \
                                '<return_msg><![CDATA[OK]]></return_msg>' \
                                '</xml>' 


                    # 邀请码用户送抵用券 2015-10-24
                    #invitation = db_user.get('invitation', '')
                    #if invitation!='' and db_user.get('invite_coupon_has_sent', 0)==0: # 已填邀请码并且未送过券
                    #    #coupon_user = db.app_user .find_one({'my_invit_code':invitation},{'uname':1})
                    #    coupon_user = app_user_helper.get_user_by_invit_code(invitation)
                    #    if coupon_user:
                    #        # 送邀请码用户抵用券
                    #        # 使用新抵用券 2016-02-29, gt
                    #        print '送邀请码用户抵用券'
                    #        try:
                    #            settings_helper.give_coupon_to_user(
                    #                coupon_active_code = app_helper.COUPON_SET['INVIT_ORDER'],
                    #                uname=coupon_user['uname'],
                    #                unionid=coupon_user.get('unionid','')
                    #            )
                    #        except Exception, e:
                    #            print 'Error', e
                    #            traceback.print_exc()
                    #            pa#ss

                    #        # 设置已送标志
                    #        db.app_user.update_one({'uname':r['uname']}, {'$set':{
                    #            'invite_coupon_has_sent':1,
                    #            'last_status' : int(time.time()),
                    #        }})
                    
                    b2 = r['cart']
                    b2s = [] # 除 mall 订单外，其他订单 cart_list为空

                    if r['type'] in ['TUAN', 'SINGLE']: #order_id[0]=='t': # 拼团订单处理
                        # 不修改购物车内容
                        status, comment = pt_succ.process_tuan_after_paid(r, 'wxpay')

                    elif r['type'] == 'MALL': # 商家订单
                        b2s = pt_succ.process_mall_after_paid(r, 'wxpay')

                    else: # 普通1小时订单: n开头、e开头

                        b2 = pt_succ.process_1hour_after_paid(r, 'wxpay', status)

                    # 推送通知
                    #if len(r['uname'])==11 and r['uname'][0]=='1':
                    #   jpush.jpush('已收到您的付款，我们会尽快处理。', r['uname'])

                    # 有些状态修改会比较快，避免异步操作造成的状态错误
                    r8 = db.order_app.find_one_and_update(
                        {
                            'order_id' : order_id,
                            'status' : {'$in':['DUE', 'PREPAID', 'TIMEOUT']},
                        },
                        {
                            '$set' : {
                                'status' : status,
                                status   : int(time.time()),
                            },
                        },
                        {'order_id':1}
                    )
                    if r8==None:
                        print '订单状态已改变，未修改:', status, order_id.encode('utf-8')
                    else:
                        print '订单状态修改:', status, order_id.encode('utf-8')

                else:
                    print "重复通知：wxpay"
                    b2 = r['cart']
                    b2s = []
                    used_balance = {
                        'credit' : float(r.get('credit_cash_used',0)),
                        'return_cash' : float(r.get('return_cash_used',0)),
                    }


                # 修改订单状态
                t = xml.find('time_end').text
                paid_time = '%s-%s-%s %s:%s:%s' % (t[:4],t[4:6],t[6:8],t[8:10],t[10:12],t[12:])
                db.order_app.update_one({'order_id':order_id},{
                    '$set'  : {
                        #'status'       : status,
                        'cart'         : b2,     # 更新购物车  2015-09-11
                        'cart_list'    : b2s,    # 只有mall订单有数据
                        'wx_trade_no'  : transaction_id,
                        'paid_time'    : paid_time,
                        'paid_tick'    : int(time.time()),
                        'wx_out_trade_no'  : order_id0,
                        'pay_type'     : 'WXPAY_CREDIT' if float(r.get('use_credit', '0'))>0 else 'WXPAY',
                        'credit_total' : '%.2f' % float(r.get('use_credit', '0')),
                        'credit_cash_used' : '%.2f'%used_balance['credit'] if float(r.get('use_credit', '0'))>0 else '0.00',
                        'return_cash_used' : '%.2f'%used_balance['return_cash'] if float(r.get('use_credit', '0'))>0 else '0.00',
                        'wxpay_total'  : '%.2f' % (float(xml.find('total_fee').text)/100.0),
                        'wx_mch_id'  : xml.find('mch_id').text, # 保存 商户id 2016-06-29, gt
                        #status         : int(time.time()), # 2016-01-10, gt
                        'last_status'  : int(time.time()), 
                    },
                    '$push' : {
                        'wx_notify' : str_xml,
                        'history'   : (app_helper.time_str(), 'wxpay', '已付款'+comment)
                    }
                })

                # 更新app_order_num 20160927 lf
                if status in ['PAID', 'PAID_AND_WAIT']:
                    if len(db_user.get('uname', '')) == 11:  # 手机号码下单
                        db.app_user.update_one({'uname': db_user['uname']}, {'$set': {'app_order_num': 1}})
                    elif len(db_user.get('openid', '')) > 11:  # openid下单
                        db.app_user.update_one({'openid': db_user['openid']}, {'$set': {'app_order_num': 1}})

                # 推 MQ
                if r['type'] in ['TUAN', 'SINGLE']:
                    if status == 'PAID':
                        app_helper.event_push_mq(order_id,'PAID')
                        app_helper.event_push_mq(order_id,'PT_SUCC')
                        log4u.log('WxpayNotify', log4u.PAID , '付款成功', order_id)
                        #log4u.log('WxpayNotify', log4u.PT_SUCC , '拼团成功', order_id)
                    elif status == 'PAID_AND_WAIT':
                        app_helper.event_push_mq(order_id,'PAID')
                        log4u.log('WxpayNotify', log4u.PAID_AND_WAIT , '付款成功，待成团', order_id)
                    elif status == 'FAIL_TO_REFUND':
                        app_helper.event_push_mq(order_id,'PAID') # 拼团失败也要推支付信息 2016-09-21
                        app_helper.event_push_mq(order_id,'CANCEL_TO_REFUND')
                        log4u.log('WxpayNotify', log4u.PAID , '付款成功', order_id)
                        log4u.log('WxpayNotify', log4u.SYS_CANCEL_ORDER , '订单取消', order_id)
                    else:
                        print '不该出现的状态', str(status)
                else:
                    if status == 'PAID':
                        app_helper.event_push_mq(order_id,'PAID')
                        log4u.log('WxpayNotify', log4u.PAID , '付款成功', order_id)
                    else:
                        print '不该出现的状态', str(status)


        return  '<xml>' \
            '<return_code><![CDATA[SUCCESS]]></return_code>' \
            '<return_msg><![CDATA[OK]]></return_msg>' \
            '</xml>' 

##-----------------------------------------------------------------

# 取得主机端口
class WxGetHost:
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(openid='',session_id='')

        if param.openid=='' and param.session_id=='':
            return json.dumps({'ret' : -2, 'msg' : '参数错误1'})

        # 同时支持openid和session_id
        if param.openid!='':
            uname = app_helper.check_openid(param.openid)
        else:
            uname = app_helper.wx_logged(param.session_id)
        if uname:
            # 返回host地址、端口
            host = setting.app_pool[random.randint(0,len(setting.app_pool)-1)]
            print 'host = ', host
            return json.dumps({'ret' : 0, 'data' : {
                'protocol' : 'http',
                #'host'     : setting.app_host, #'app.urfresh.cn',
                'host'     : host,
                'port'     : '12050',
            }})
        else:
            return json.dumps({'ret' : -4, 'msg' : '无效的openid'})



#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
