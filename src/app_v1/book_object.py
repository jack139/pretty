#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper
from libs import checkout_helper

db = setting.db_web

# 订阅
url = ('/app/v1/book_object')

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

        r = checkout_helper.checkout_obj(uname, param.object_id)
        if r['ret']<0:
            return json.dumps({'ret' : r['ret'], 'msg' : r['msg']})            

        ret_data = {
            "object_id" : param.object_id,     # 唯一代码 
            "type"  : 1 if r['obj_type']=='course' else 2,  # 类型： 1 课程, 2 专辑 
            "title" : r['title'],
            "due"   : r['due'],  # 应付金额，单位 分 , 默认1分
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
