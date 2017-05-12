#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 增加／删除店员
url = ('/app/v1/employee_add')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','employee_tel','action'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', employee_tel='', tick='', action='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick, 
            param.employee_tel, param.action):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        if param['action'].upper() not in ('ADD', 'DEL'):
            return json.dumps({'ret' : -7, 'msg' : '无效的action取值'})

        # 检查店员电话号码
        r2 = db.app_user.find_one({'uname':param['employee_tel']})
        if r2 is None:
            return json.dumps({'ret' : -5, 'msg' : 'employee_tel未注册'})

        r3 = db.employee_auth.find_one({'owner_userid':uname['userid'],'employee_userid':r2['userid']})

        if param['action'].upper()=='ADD':
            if r3:
                return json.dumps({'ret' : -8, 'msg' : '店员已添加'})

            # 建立店主店员关系
            db.employee_auth.insert_one({
                'owner_userid'    : uname['userid'],
                'employee_userid' : r2['userid'],
                'object_list'     : [],
                'time'            : app_helper.time_str(),
            })
        else:
            if r3:
                # 删除关系
                db.employee_auth.delete_one({'owner_userid':uname['userid'],'employee_userid':r2['userid']})
                # 还应删除相关的学习进度什么的！待实现

        # 返回
        return json.dumps({
            'ret'  : 0,
        })
