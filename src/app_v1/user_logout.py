#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/user_logout')

# 退出
class handler: # Logout:
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', session='', dev_id='', ver_code='', sign='')

        if '' in (param.app_id, param.session, param.dev_id, param.ver_code, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.dev_id, param.ver_code, param.session])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        session = app_helper.get_session(param.session)
        if session==None:
           return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        db.app_sessions.delete_one({'session_id':param.session})

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'logout' : True,
            }
        })
