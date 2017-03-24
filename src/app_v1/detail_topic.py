#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 专辑详情
url = ('/app/v1/detail_topic')

# 退出
class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "object_id" : param.object_id,     # 唯一代码 
            "title" : "专辑标题",
            "title2" : "专辑副标题专辑副标题",
            "abstract" : "专辑简介正文专辑简介正文专辑简介正文专辑简介正文专辑简介正文",
            "topic_image" : "https://pretty.f8cam.com/static/image/banner/course.png",     # 专辑图片url 
            "course" : [
                {
                    "object_id" : "300001",  # 内部唯一标识 
                    "title" : "课程标题",
                    "title2" : "课程副标题课程副标题",
                    "speaker" : "讲师名",
                    "type" : 2,  # 1- 视频   2 － 音频  
                    "image" : "https://pretty.f8cam.com/static/image/banner/course.png",  # 课程主图 
                    "length" : 90,  # 长度，单位：分钟 
                    "price" : 100000,  # 价格，整数，单位：分 
                    "volume" : 10000,  # 销量，整数 
                },
                {
                    "object_id" : "300002",  # 内部唯一标识 
                    "title" : "课程标题2",
                    "title2" : "课程副标题课程副标题2",
                    "speaker" : "讲师名",
                    "type" : 1,  # 1- 视频   2 － 音频  
                    "image" : "https://pretty.f8cam.com/static/image/banner/course.png",  # 课程主图 
                    "length" : 120,  # 长度，单位：分钟 
                    "price" : 200000,  # 价格，整数，单位：分 
                    "volume" : 20000,  # 销量，整数 
                },
            ],
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
