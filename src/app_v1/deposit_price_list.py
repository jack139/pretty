#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/deposit_price_list')

# 获取充值价格列表（不需要session）
class handler: 
    @app_helper.check_sign(['app_id', 'dev_id', 'ver_code', 'tick'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #--------------------------------------------------

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'price_list' : app_helper.DEPOSIT_PRICE_LIST,
            }
        })
