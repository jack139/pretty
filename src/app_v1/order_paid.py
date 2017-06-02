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

        #-------------------------------------------------- 待实现

        ret_data = {
            "order_trade_id" : param.order_trade_id,
            "due"      : 1000,         # 应付金额，单位 分
            "paid"     : 1000,         # 实付金额 
            "status"   : "PENDING",     # 订单状态：PAID/PENDING 已支付／未支付
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
