#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 授权课程给店员,
url = ('/app/v1/employee_auth_to')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','userid','object_id','action'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='', 
            userid='', object_id='', action='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, param.tick, 
            param.userid, param.object_id, param.action):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        if param['action'].upper() not in ['AUTH','CANCEL']:
            return json.dumps({'ret' : -7, 'msg' : '无效的action取值'})

        r4 = db.obj_store.find_one({'obj_id':param['object_id']})
        if r4 is None:
            return json.dumps({'ret' : -6, 'msg' : '无效的object_id'})

        # userid 支持多个，用英文逗号分隔
        userid_list = param['userid'].split(',')
        r4 = db.employee_auth.find({'owner_userid':uname['userid'],
            'employee_userid': {'$in' : userid_list}})
        #if r3 is None:
        #    return json.dumps({'ret' : -5, 'msg' : '此userid不是当前店主的店员'})

        for r3 in r4: # 操作多个店员
            if param['action'].upper()=='AUTH': # 添加
                if param['object_id'] not in r3['object_list']:
                    db.employee_auth.update_one({'_id':r3['_id']},
                        {'$push' : {'object_list' : param['object_id']}}
                    )
            else: # 删除
                if param['object_id'] in r3['object_list']:
                    r3['object_list'].remove(param['object_id'])
                    db.employee_auth.update_one({'_id':r3['_id']},
                        {'$set' : {'object_list' : r3['object_list']}}
                    )

        # 返回
        return json.dumps({
            'ret'  : 0,
        })
