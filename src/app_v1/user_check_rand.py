#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper
#from libs import app_user_helper

db = setting.db_web

url = ('/app/v1/user_check_rand')

# 检查随机码: 注册／找回密码时
class handler: # CheckRand:
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','rand','passwd'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        #print web.input()
        param = web.input(app_id='', session='', rand='', passwd='', dev_id='', ver_code='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.rand, param.passwd, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        return self.check_rand(param, version)

    @staticmethod
    def check_rand(param, version='v1'):
        session = app_helper.get_session(param.session)
        if session==None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        if session.get('pwd_fail',0)>=5:
            print '========> 请重新获取验证码', session.get('pwd_fail',0)
            return json.dumps({'ret' : -5, 'msg' : '请重新获取验证码'})

        #if param.rand.strip()!=session['rand']: # 测试，不检查校验码
        if param.rand.strip()!='9998':
            #2015-12-22,gt
            if session['uname'] in app_helper.INNER_NUM.keys() and param.rand.strip()==app_helper.INNER_NUM[session['uname']]:
                pass
            else:
                db.app_sessions.update_one({'session_id':session['session_id']},{'$inc':{'pwd_fail':1}})
                return json.dumps({'ret' : -5, 'msg' : '短信验证码错误'})

        db.app_sessions.update_one({'session_id':session['session_id']},{'$set':{
            'login'  : 1,
            'attime' : time.time(),
        }})


        # 更新登录时间 2016-12-28， gt
        db.app_user.update_one({'uname' : session['uname']}, {'$set' : {
            'last_time' : app_helper.time_str(),
            'passwd'    : app_helper.my_crypt(param.passwd),
            'reg_ok'    : 1, # 标记已注册成功，reg_ok==0属于注册过程中的 2016-06-21
        }})


        ## 返回

        return json.dumps({
            'ret'  : 0,
            'data' : {
                'session' : session['session_id'],
                'login'   : True,
                'uname'   : session['uname'],
                'alert'   : True,  # 
                'message' : '测试弹窗',
            }
        })
