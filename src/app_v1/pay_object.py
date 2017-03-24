#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 支付
url = ('/app/v1/pay_object')

# 退出
class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id',
            'pay_type','order_id','total'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', 
            pay_type='', order_id='', total='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, 
            param.pay_type, param.total, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "pay_type"    : 0, # 支付类型 
            "pass_to_pay" : 0, # 是否可支付：0 不可支付，1 可支付 
            "order_id"    : "a000001", # 生成的订单号，pass_to_pay==0时无订单号 
            "msg"         : "余额不足",  # pass_to_pay==0时的提示信息
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
