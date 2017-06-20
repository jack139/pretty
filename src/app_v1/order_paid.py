#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 支付完成
url = ('/app/v1/order_paid')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','order_trade_id','data'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', order_trade_id='', data='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.order_trade_id, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        # 检查订单状态－－－－－－ 待实现

        # 修改充值订单状态
        r2 = db.order_recharge.find_one_and_update(
            {'recharge_id' : param.order_trade_id},  # 实充值订单号
            {
                '$set' : {'status':'PREPAY'},
                '$push' : {'order_paid_data':param.data},
            },
        )

        if r2 is None:
            return json.dumps({'ret' : -3, 'msg' : '未找到订单'})

        # 如果是IAP订单，使用data数据检查支付情况，backrun异步检查
        if r2['pay_type']=='iap':
            app_helper.event_push_notify('iap', [param.order_trade_id, param.data])

        ret_data = {
            "order_trade_id" : param.order_trade_id,
            "due"      : r2['due'],         # 应付金额，单位 分
            "paid"     : r2['due'],         # 实付金额 
            "status"   : "PENDING",     # 订单状态：PAID/PENDING 已支付／待支付
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })


'''
IAP 校验结果

{
    u'status': 0, 
    u'environment': u'Sandbox', 
    u'receipt': {
        u'download_id': 0, 
        u'adam_id': 0, 
        u'request_date': u'2017-06-19 03:19:56 Etc/GMT', 
        u'app_item_id': 0, 
        u'original_purchase_date_pst': u'2013-08-01 00:00:00 America/Los_Angeles', 
        u'version_external_identifier': 0, 
        u'receipt_creation_date': u'2017-06-17 07:27:09 Etc/GMT', 
        u'in_app': [
            {
                u'is_trial_period': u'false', 
                u'purchase_date_pst': u'2017-06-17 00:27:09 America/Los_Angeles', 
                u'product_id': u'com.006.pay', 
                u'original_transaction_id': u'1000000307992143', 
                u'original_purchase_date_pst': u'2017-06-17 00:27:09 America/Los_Angeles', 
                u'original_purchase_date': u'2017-06-17 07:27:09 Etc/GMT', 
                u'original_purchase_date_ms': u'1497684429000', 
                u'purchase_date': u'2017-06-17 07:27:09 Etc/GMT', 
                u'purchase_date_ms': u'1497684429000', 
                u'transaction_id': u'1000000307992143', 
                u'quantity': u'1'
            }
        ], 
        u'original_purchase_date_ms': u'1375340400000', 
        u'original_application_version': u'1.0', 
        u'original_purchase_date': u'2013-08-01 07:00:00 Etc/GMT', 
        u'request_date_ms': u'1497842396474', 
        u'bundle_id': u'com.nuoyin.app', 
        u'receipt_creation_date_pst': u'2017-06-17 00:27:09 America/Los_Angeles', 
        u'application_version': u'1.0', 
        u'request_date_pst': u'2017-06-18 20:19:56 America/Los_Angeles', 
        u'receipt_creation_date_ms': u'1497684429000', 
        u'receipt_type': u'ProductionSandbox'
    }
}
'''