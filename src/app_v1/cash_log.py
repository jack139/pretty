#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的购买记录
url = ('/app/v1/cash_log')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        r2 = db.order_trade.find({'userid':uname['userid']}, sort=[('_id',-1)])

        orders = []
        for i in r2:
            if i['trade_type']=='consume':
                sign = -1
            else:
                sign = 1
            orders.append({
                "action" : i['comment'],
                "cash" : i['total_sum']*sign, # 金额，单位 分
                "date" : i['pay_time'], # 发生时间 
                "order_id" : i['order_trade_id'], # 订单号
            })

        ret_data = {
           "order" : orders
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
