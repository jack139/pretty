#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 获取系统消息
url = ('/app/v1/system_info')

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


        # 准备返回值
        ret_data =  {
            "info" : [
                {
                    "info_id" : "abcd",  # 消息id 
                    "title" : "测试消息1",
                    "content" : "消息内容",
                    "time_str" : "2017-08-09 20:20:20",  # 时间 
                },
                {
                    "info_id" : "abef",  
                    "title" : "测试消息2",
                    "content" : "消息内容",
                    "time_str" : "2017-08-09 12:12:12",
                },
            ]
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
