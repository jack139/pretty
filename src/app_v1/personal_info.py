#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 个人信息
url = ('/app/v1/personal_info')

# 退出
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
            "name" : "用户昵称",
            "image" : "https://pretty.f8cam.com/static/image/test/head.png",   # 用户头像 
            "tel" : "18911111111", # 用户注册手机号 
            "wx_login" : 0, # 是否微信登录 0 不是， 1 是 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
