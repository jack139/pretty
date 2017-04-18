#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time, traceback, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/user_pwd_login')


# 密码登录
class handler: 

    @app_helper.check_sign(['app_id','dev_id','ver_code','tick', 'mobile', 'passwd'])
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='', mobile='', passwd='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick, param.mobile, param.passwd):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        number = param.mobile.strip()
        if len(number)<11 or (not number.isdigit()):
            return json.dumps({'ret' : -10, 'msg' : '手机号码格式错误'})

        if number in app_helper.BLOCK_LIST:
            return json.dumps({'ret' : -10, 'msg' : '手机号码错误'})

        # 根据openid检查用户是否存在
        db_user = db.app_user.find_one_and_update({'uname':number},{'$set':{
            'app_id'      : param['app_id'],
            'last_status' : int(time.time()),
        }})
        if db_user==None:
            # 未注册，新建用户记录, 
            return json.dumps({'ret' : -5, 'msg' : '手机号未注册'})

        if db_user.get('pwd_fail_timeout',0)>int(time.time()):
            return json.dumps({'ret' : -9, 'msg' : '密码连续错误5次，帐户锁定15分钟'})

        if db_user.get('passwd')!=app_helper.my_crypt(param.passwd):
            pwd_fail = db_user.get('pwd_fail',0)+1
            if pwd_fail==5:
                pwd_fail_timeout = int(time.time())+900 # 锁定15分钟
            elif db_user.get('pwd_fail',0)>5: # 重新计次
                pwd_fail_timeout = 0
                pwd_fail = 1                
            else: # 未到5次，只计次，不锁定
                pwd_fail_timeout = 0
            db.app_user.update_one({'uname':number},{'$set':{
                'pwd_fail_timeout' : pwd_fail_timeout, 
                'pwd_fail' : pwd_fail
            }})
            return json.dumps({'ret' : -7, 'msg' : '密码错误'})
        else:
            db.app_user.update_one({'uname':number},{'$set':{
                'pwd_fail_timeout' : 0,
                'pwd_fail' : 0,
            }})

        # 添加session
        import os
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = 'f6102bff8451236b8ca1'
        session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
        session_id = session_id.hexdigest()

        db.app_sessions.insert_one({
            'session_id' : session_id,
            'userid'     : db_user['userid'],
            'uname'      : number,
            'login'      : 1,
            'ip'         : web.ctx.ip,
            'attime'     : now,
            'type'       : 1,
            'pwd_fail'   : 0,
            'bind'       : 1, # 电话用户本身就认为是绑定的
        })

        alert = False
        message = ''

        return json.dumps({'ret': 0, 'data': {
            'session_id' : session_id,
            'alert'      : alert,
            'message'    : message,
        }})


