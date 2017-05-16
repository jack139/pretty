#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 课程已授权的店员列表
url = ('/app/v1/object_auth_list')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='', object_id='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick, param.object_id):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        # 生成数据
        user_list = []
        # 只返回当前用户为店主的所属用户列表
        r3 = db.employee_auth.find({'object_list':param.object_id, 'owner_userid':uname['userid']})
        for i in  r3:
            r4 = db.app_user.find_one({'userid':i['employee_userid'],'type':1}) # 电话用户
            if r4 is None:
                continue
            user_list.append({
                'userid' : r4['userid'],
                'real_name' : r4.get('vip_realname',''),
                'mobile_num' : r4['uname'], 
            })

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : { 'employee': user_list },
        })
