#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 支付完成
url = ('/wx/order_paid')

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', order_trade_id='', data='')

        if param.order_trade_id=='':
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        #--------------------------------------------------


        # 修改充值订单状态
        r2 = db.order_recharge.find_one_and_update(
            {'recharge_id' : param.order_trade_id},  # 实充值订单号
            {
                '$set' : {'status':'PREPAY'},
                '$push' : {'order_paid_data':param.data},
            },
        )

        ret_data = {
            "order_trade_id" : param.order_trade_id,
            "due"      : r2['due'],         # 应付金额，单位 分
            "paid"     : r2['due'],         # 实付金额 
            "status"   : "PENDING",     # 订单状态：PAID/PENDING 已支付／未支付
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
