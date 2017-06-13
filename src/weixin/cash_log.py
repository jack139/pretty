#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的购买记录
url = ('/wx/cash_log')

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='')

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

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
