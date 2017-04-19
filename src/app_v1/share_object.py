#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 分享页面链接
url = ('/app/v1/share_object')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

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
