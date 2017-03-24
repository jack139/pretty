#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 精品专辑列表
url = ('/app/v1/list_topic')

# 退出
class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','page_size','page_index'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', page_size='', page_index='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.page_size, param.page_index, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "topic" : [
                {
                    "object_id" : "300001",  # 内部唯一标识 
                    "title" : "专辑标题",
                    "title2" : "专辑副标题专辑副标题专辑副标题",
                    "type" : 1,  # 1- 视频   2 － 音频  
                    "image" : "https://pretty.f8cam.com/static/image/banner/course.png",  # 课程主图 
                    "length" : 5,  # 长度，单位：分钟 
                },
                {
                    "object_id" : "300002",  # 内部唯一标识 
                    "title" : "专辑标题2",
                    "title2" : "专辑副标题专辑副标题专辑副标题2",
                    "type" : 2,  # 1- 视频   2 － 音频  
                    "image" : "https://pretty.f8cam.com/static/image/banner/course.png",  # 课程主图 
                    "length" : 15,  # 长度，单位：分钟 
                },
            ],
            "total" : 2, # 返回的课程数量，小于 page_size说明到末尾 
            "page_size" : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
