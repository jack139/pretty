#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib3, urllib, json
from config import setting
#import app_helper

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

    r = pool.urlopen('POST', url, body=urllib.unquote_plus(base64_data))

    if r.status==200:
        return json.loads(r.data)
    else:
        print 'Error: HTTP CODE', r.status
        return None


# 处理付款通知
def process_pay_notify(event):
    pay_type = event['data']['type']
    pay_data = event['data']['data']

    if pay_type=='iap':
        return process_iap_notify(pay_data[0], pay_data[1]) # 订单号， 校验数据
    elif pay_type=='alipay':
        return process_alipay_notify(pay_data)
    elif pay_type=='wxpay':
        return process_wxpay_notify(pay_data)
    else:
        print 'Error: 未知付款类型', pay_type

    return 'FAIL', '未知付款类型'


# 按id查找充值价格表
def find_deposit_price(price_id):
    for i in DEPOSIT_PRICE_LIST:
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
    check_data = iap_check(pay_data)
    if check_data is None:
        return 'WAIT', '校验数据失败' # 置为 WAIT, 重新校验，backrun会控制重试10次

    # 检查实际充值金额与订单提交的是否一致
    r2 = db.order_recharge.find_one({'recharge_id' : order_id})
    if r2 is None:
        return 'FAIL', '未找到订单'

    price_item = find_deposit_price(check_data['receipt']['in_app']['product_id'])
    if price_item is None:
        db.order_recharge.update_one({'recharge_id' : order_id},
            {
                '$set' : {'status':'FAIL'},
                '$push' : {'process_notify_msg' : (helper.time_str(),'价格id错误')},
            }
        )
        return 'FAIL', '价格id错误'

    if int(r2['due'])!=int(check_data['receipt']['in_app']['quantity'])*price_item['price']:
        db.order_recharge.update_one({'recharge_id' : order_id},
            {
                '$set' : {'status':'FAIL'},
                '$push' : {'process_notify_msg' : (helper.time_str(),'充值金额不相符')},
            }
        )
        return 'FAIL', '充值金额不相符'

    # 充值操作
    order_trade_id = credit_helper.save_to_balance(r2['userid'], int(r2['due']))

    # 修改充值订单状态
    db.order_recharge.update_one({'recharge_id' : order_id},
        {
            '$set' : {
                'status':'PAID', 
                'order_trade_flow_id':order_trade_id
            },
            '$push' : {'process_notify_msg' : (helper.time_str(),'支付完成')},
        }
    )

    return 'DONE', '支付完成'

