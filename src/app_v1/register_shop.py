#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 提交认证店主
url = ('/app/v1/register_shop')

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

        r2 = db.app_user.find_one({'userid':uname['userid'], 'type':1})
        if r2 and r2.get('upload_licence','')=='':
            return json.dumps({'ret' : -5, 'msg' : '未上传营业执照照片'})

        # 设置店主审核状态
        db.app_user.update_one({'userid':uname['userid'], 'type':1},{'$set':{
            'user_role' : 3,
            'user_role_status' : 'WAIT',
        }})

        # 返回
        return json.dumps({
            'ret'  : 0,
        })
