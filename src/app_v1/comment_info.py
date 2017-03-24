#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 获取学员评价
url = ('/app/v1/comment_info')

# 退出
class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id','page_size','page_index'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', 
            page_size='', page_index='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, 
            param.page_size, param.page_index, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "comment" : [
                {
                    "name" : "学员名",
                    "image" : "http:///…../1.png", # 头像 
                    "star" : 5,  # 评的星级 
                    "time" : "19天前", 
                },
                {
                    "name" : "学员名2",
                    "image" : "http:///…../1.png", # 头像 
                    "star" : 1,  # 评的星级 
                    "time" : "2017-01-01", 
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
