#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 余额充值
url = ('/app/v1/deposit_cash')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','pay_sum','pay_type'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='', pay_sum='', pay_type='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick, 
            param.pay_sum, param.pay_type):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------  待实现

        ret_data = {
            "order_trade_id" : 'can_not_use',  
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
