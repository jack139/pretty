#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的购买记录
url = ('/app/v1/order_list')

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

        ret_data = {
           "order" : [
                {
                    "action" : "课程名称",
                    "cash" : -499, # 金额，单位 分
                    "date" : "2017-03-12 17:00", # 发生时间 
                    "order_id" : "n00001", # 订单号
                },
                {
                    "action" : "充值",
                    "cash" : 10000, # 金额，单位 分 
                    "date" : "2017-03-12 17:00", # 发生时间 
                    "order_id" : "d00002", # 充值订单号
                },
            ]
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
