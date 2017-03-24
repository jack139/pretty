#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的收藏列表
url = ('/app/v1/heart_list')

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
            "heart" : [
                {
                    "object_id" : "100001",
                    "title" : "课程标题1",
                    "type" : 1,  # 类型： 1 课程, 2 专辑 
                    "object_type" : 1,  # 1- 视频   2 － 音频  
                    "length" : 90, # 长度，单位 分钟 
                    "progress" : 30, # 进度百分比，如果是未购买课程，此字段为-1
                },
                {
                    "object_id" : "100002",
                    "title" : "课程标题2",
                    "type" : 2, 
                    "object_type" : 1,
                    "length" : 20,
                    "progress" : 0,
                },
                {
                    "object_id" : "100003",
                    "title" : "课程标题3",
                    "type" : 1, 
                    "object_type" : 2,
                    "length" : 190,
                    "progress" : -1,
                },
            ]
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
