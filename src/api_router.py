#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os, gc
import time, json, hashlib, random
import rsa, base64
import traceback 
from config import setting
import app_helper 
from libs import log4u

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


db = setting.db_primary  # 默认db使用web本地

urls = [
    '/app/v1/first_hand',  'FisrtHand_v2',
    '/app/v1/get_host',    'GetHost',
    '/app/alipay_notify',   'AlipayNotify',
    '/app/wxpay_notify',    'WxpayNotify',
]

app = web.application(urls, globals())
application = app.wsgifunc()

#----------------------------------------

gc.set_threshold(300,5,5)

###########################################

def my_rand(n=8):
    return ''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for ch in range(n)])

########### APP接口 #######################################################

## 需优化内容：
# 1. 出错info页面要做微信端优化 --> 直接跳转回init页面
# 2. urlopen, json.loads 需要处理异常！


# 常量
public_key='312045ED9D036BEED16E96F3878E222ED7E58AC9'


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
        param=web.input(type='', dev_id='', ver_code='', tick='', sign='')

        print web.data()

        if '' in (param.type, param.dev_id, param.ver_code, param.tick, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.type not in ['IOS', 'ANDROID']:
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        sign_str = '%s%s%s%s%s' % (public_key, param.type, param.dev_id, param.ver_code, param.tick)
        md5_str = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        # 注册新app
        app_id = my_rand().upper()
        if db.app_device.find({'app_id' : app_id}).count()>0:
            # 两次随机仍重复的可能性，很小吧
            app_id = my_rand().upper()
        private_key = app_helper.my_crypt(app_id).upper()
        db.app_device.insert_one({
            'app_id'      : app_id, 
            'private_key' : private_key, 
            'type'        : param.type,
            'dev_id'      : param.dev_id,
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
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 返回host地址、端口
        if param.app_id in GREY_TEST:
            host = 'xxx.test.com'
        else:
            host = setting.app_pool[random.randint(0,len(setting.app_pool)-1)]
        print 'host = ', host
        return json.dumps({'ret' : 0, 'data' : {
            'url_host' : 'https://%s:17213'%host,
        }})


### ----------------------------------------------------------------------------------------------------



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

        app_helper.event_push_notify('alipay', param, order_id)

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

        order_id = ''
        
        if return_code=='SUCCESS': # 有付款
            order_id0 = xml.find('out_trade_no').text
            order_id = order_id0.split('_')[0]

        app_helper.event_push_notify('wxpay', str_xml, order_id)

        return  '<xml>' \
            '<return_code><![CDATA[SUCCESS]]></return_code>' \
            '<return_msg><![CDATA[OK]]></return_msg>' \
            '</xml>' 

##-----------------------------------------------------------------



#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
