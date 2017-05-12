#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 店员已授权的课程
url = ('/app/v1/employee_auth_list')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','userid'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='', userid='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick, param.userid):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        # 生成数据
        object_list = []
        r3 = db.employee_auth.find_one({'owner_userid':uname['userid'],'employee_userid':param.userid})
        if r3:
            for i in r3['object_list']:
                r4 = db.obj_store.find_one({'obj_id':i})
                if r4 is None:
                    continue
                object_list.append({
                    'object_id' : r4['obj_id'],
                    'course_name' : r4.get('title'),
                    'auth_num' : 0, # 已授权店员数 ,, ---------------- 待实现
                })

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : { 'course': object_list },
        })
