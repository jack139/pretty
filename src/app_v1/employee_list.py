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
            # 统计此店员完成课程输量
            complete_num = 0
            for j in i['object_list']:
                r5 = db.progress_info.find_one({'userid':i['employee_userid'], 'obj_id':j})
                if r5 and r5['progress']==100:
                    complete_num += 1

            # 获取店员信息
            r4 = app_helper.get_user_detail(i['employee_userid'])

            employee.append({
                'userid'       : i['employee_userid'],
                'real_name'    : r4.get('real_name',''),
                'auth_num'     : len(i['object_list']),
                'complete_num' : complete_num, # 完成课程数,
                'employee_tel' : r4.get('mobile',''), # 注册的号码
            })

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : { 'employee': employee },
        })
