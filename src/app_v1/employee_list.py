#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 已授权店员清单
url = ('/app/v1/employee_list')

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

        # 生成数据
        employee = []
        r3 = db.employee_auth.find({'owner_userid':uname['userid']})
        for i in r3:
            r4 = app_helper.get_user_detail(uname['userid'])
            employee.append({
                'userid'    : i['employee_userid'],
                'real_name' : r4.get('real_name',''),
                'auth_num'  : len(i['object_list']),
                'complete_num' : 0, # 完成课程数,, ---------------- 待实现
            })

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : { 'employee': employee },
        })
