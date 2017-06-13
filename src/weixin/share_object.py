#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 分享页面链接
url = ('/wx/share_object')

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', object_id='')

        if param.object_id=='':
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        #--------------------------------------------------

        r3 = db.obj_store.find_one({
            'obj_id' : param.object_id, 
        })
        if r3 is None:
            return json.dumps({'ret' : -5, 'msg' : '错误的object_id'})

        if len(r3['image'])>0: # 取第1张图, 
            image_url = app_helper.image_url(r3['image'][0])
        else:
            image_url = ''

        ret_data = {
            "object_id"     : param.object_id,     # 唯一代码 
            "type"          : 1 if r3['media']=='video' else 2,  # 类型： 1 课程, 2 专辑 
            "share_title"   : r3['title'],
            "share_content" : r3['description'],
            "share_img"     : image_url,  # 分享图片 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
