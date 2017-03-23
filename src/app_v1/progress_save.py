#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 保存学习进度
url = ('/app/v1/progress_save')

# 退出
class handler: 
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', progress='', sign='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, 
            param.progress, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.dev_id, param.ver_code, 
            param.session, param.object_id, param.progress])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {}

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
