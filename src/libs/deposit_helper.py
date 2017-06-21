#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib3, urllib, json
from config import setting
import app_helper
from libs import credit_helper

urllib3.disable_warnings()

db = setting.db_web

SANDBOX = True

def iap_check(base64_data):

    pool = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)

    # sandbox
    if SANDBOX:
        url = 'https://sandbox.itunes.apple.com/verifyReceipt'
    else:
        url = 'https://buy.itunes.apple.com/verifyReceipt'

    print url

    post_data = json.dumps({'receipt-data' : urllib.unquote_plus(base64_data)})
    r = pool.urlopen('POST', url, body=post_data)

    if r.status==200:
        print r.data
        return json.loads(r.data)
    else:
        print 'Error: HTTP CODE', r.status
        return None


# 处理付款通知
def process_pay_notify(event):
    pay_type = event['data']['type']
    pay_data = event['data']['data']
    order_id = event['data']['order_trade_id']

    if pay_type=='iap':
        return process_iap_notify(order_id, pay_data) # 订单号， 校验数据
    elif pay_type=='alipay':
        return process_alipay_notify(order_id, pay_data)
    elif pay_type=='wxpay':
        return process_wxpay_notify(order_id, pay_data)
    else:
        print 'Error: 未知付款类型', pay_type

    return 'FAIL', '未知付款类型'


# 按id查找充值价格表
def find_deposit_price(price_id):
    for i in app_helper.DEPOSIT_PRICE_LIST:
        if i['product_id']==price_id:
            return i
    return None

# 处理 iap 付款通知
#IAP 校验结果
#{
#    u'status': 0, 
#    u'environment': u'Sandbox', 
#    u'receipt': {
#        u'download_id': 0, 
#        u'adam_id': 0, 
#        u'request_date': u'2017-06-19 03:19:56 Etc/GMT', 
#        u'app_item_id': 0, 
#        u'original_purchase_date_pst': u'2013-08-01 00:00:00 America/Los_Angeles', 
#        u'version_external_identifier': 0, 
#        u'receipt_creation_date': u'2017-06-17 07:27:09 Etc/GMT', 
#        u'in_app': [
#            {
#                u'is_trial_period': u'false', 
#                u'purchase_date_pst': u'2017-06-17 00:27:09 America/Los_Angeles', 
#                u'product_id': u'com.006.pay', 
#                u'original_transaction_id': u'1000000307992143', 
#                u'original_purchase_date_pst': u'2017-06-17 00:27:09 America/Los_Angeles', 
#                u'original_purchase_date': u'2017-06-17 07:27:09 Etc/GMT', 
#                u'original_purchase_date_ms': u'1497684429000', 
#                u'purchase_date': u'2017-06-17 07:27:09 Etc/GMT', 
#                u'purchase_date_ms': u'1497684429000', 
#                u'transaction_id': u'1000000307992143', 
#                u'quantity': u'1'
#            }
#        ], 
#        u'original_purchase_date_ms': u'1375340400000', 
#        u'original_application_version': u'1.0', 
#        u'original_purchase_date': u'2013-08-01 07:00:00 Etc/GMT', 
#        u'request_date_ms': u'1497842396474', 
#        u'bundle_id': u'com.nuoyin.app', 
#        u'receipt_creation_date_pst': u'2017-06-17 00:27:09 America/Los_Angeles', 
#        u'application_version': u'1.0', 
#        u'request_date_pst': u'2017-06-18 20:19:56 America/Los_Angeles', 
#        u'receipt_creation_date_ms': u'1497684429000', 
#        u'receipt_type': u'ProductionSandbox'
#    }
#}
def process_iap_notify(order_id, pay_data):
    print 'IAP付款校验', order_id

    check_data = iap_check(pay_data)
    if check_data is None:
        print 'process_iap_notify: 校验数据失败'
        return 'WAIT', '校验数据失败' # 置为 WAIT, 重新校验，backrun会控制重试10次

    # 检查实际充值金额与订单提交的是否一致
    r2 = db.order_recharge.find_one({'recharge_id' : order_id})
    if r2 is None:
        print 'process_iap_notify: 未找到订单'
        return 'FAIL', '未找到订单'

    if check_data['status']!=0:
        print 'process_iap_notify: 数据校验失败 status=%d'%check_data['status']
        return 'FAIL', '数据校验失败 status=%d'%check_data['status']

    print 'status', r2['status']

    if r2['status']=='PAID':
        print 'process_iap_notify: 此单已充值'
        return 'DONE', '此单已充值'

    price_item = find_deposit_price(check_data['receipt']['in_app'][0]['product_id'])
    if price_item is None:
        db.order_recharge.update_one({'recharge_id' : order_id},
            {
                '$set' : {'status':'FAIL'},
                '$push' : {'process_notify_msg' : (app_helper.time_str(),'价格id错误')},
            }
        )
        print 'process_iap_notify: 价格id错误'
        return 'FAIL', '价格id错误'

    if int(r2['due'])!=int(check_data['receipt']['in_app'][0]['quantity'])*price_item['price']:
        db.order_recharge.update_one({'recharge_id' : order_id},
            {
                '$set' : {'status':'FAIL'},
                '$push' : {'process_notify_msg' : (app_helper.time_str(),'充值金额不相符')},
            }
        )
        print 'process_iap_notify: 充值金额不相符'
        return 'FAIL', '充值金额不相符'

    # 充值操作 - 按实际付款金额充值，如果做优惠，在这里修改
    order_trade_id = credit_helper.save_to_balance(r2['userid'], int(r2['due']))

    # 修改充值订单状态
    db.order_recharge.update_one({'recharge_id' : order_id},
        {
            '$set' : {
                'status':'PAID', 
                'order_trade_flow_id':order_trade_id
            },
            '$push' : {'process_notify_msg' : (app_helper.time_str(),'支付完成')},
        }
    )

    return 'DONE', '支付完成'


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
def process_alipay_notify(order_id, pay_data):
    print 'alipay 付款通知', order_id

    r2 = db.order_recharge.find_one({'recharge_id' : order_id})
    if r2 is None:
        print 'process_iap_notify: 未找到订单'
        return 'FAIL', '未找到订单'

    print 'status', r2['status']

    if r2['status']=='PAID':
        print 'process_iap_notify: 此单已充值'
        return 'DONE', '此单已充值'

    if pay_data.get('trade_status') == 'TRADE_SUCCESS' and (not pay_data.has_key('refund_status')):
        alipay_total = param.get('total_fee','0.00') # 支付宝实际支付
        alipay_total_fen = int(float(alipay_total)*100) # 单位：分
        ali_trade_no = param.get('trade_no')

        # 充值操作 - 按实际付款金额充值，如果做优惠，在这里修改
        order_trade_id = credit_helper.save_to_balance(r2['userid'], alipay_total_fen)

        # 修改充值订单状态
        db.order_recharge.update_one({'recharge_id' : order_id},
            {
                '$set' : {
                    'status':'PAID', 
                    'order_trade_flow_id':order_trade_id,
                    'ali_trade_no' : ali_trade_no,
                    'alipay_total' : alipay_total_fen, # 实际支付金额
                },
                '$push' : {'process_notify_msg' : (app_helper.time_str(),'支付完成')},
            }
        )
    else:
        print '非付款通知', order_id, pay_data.get('trade_status')

    return 'DONE', '支付完成'


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
def process_wxpay_notify(order_id, pay_data):
    print 'wxpay 付款通知', order_id

    r2 = db.order_recharge.find_one({'recharge_id' : order_id})
    if r2 is None:
        print 'process_iap_notify: 未找到订单'
        return 'FAIL', '未找到订单'

    print 'status', r2['status']
    
    if r2['status']=='PAID':
        print 'process_iap_notify: 此单已充值'
        return 'DONE', '此单已充值'

    xml=ET.fromstring(str_xml)
    result_code = xml.find('result_code').text
    if result_code=='SUCCESS': # 有付款
        wxpay_total = xml.find('total_fee').text # 微信支付实际支付，单位：分
        wxpay_total_fen = int(wxpay_total)
        wx_trade_no = xml.find('transaction_id').text

        # 充值操作 - 按实际付款金额充值，如果做优惠，在这里修改
        order_trade_id = credit_helper.save_to_balance(r2['userid'], wxpay_total_fen)

        # 修改充值订单状态
        db.order_recharge.update_one({'recharge_id' : order_id},
            {
                '$set' : {
                    'status':'PAID', 
                    'order_trade_flow_id':order_trade_id,
                    'wx_trade_no' : wx_trade_no,
                    'wxpay_total' : wxpay_total_fen, # 实际支付金额
                },
                '$push' : {'process_notify_msg' : (app_helper.time_str(),'支付完成')},
            }
        )
    else:
        print '非付款通知', order_id, pay_data.get('trade_status')

    return 'DONE', '支付完成'

