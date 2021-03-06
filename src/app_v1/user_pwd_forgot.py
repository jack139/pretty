#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper
from libs import sms

db = setting.db_web

url = ('/app/v1/user_pwd_forgot')

# 用户忘记密码
class handler: # Login2:
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','mobile'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        #print web.input()
        param = web.input(app_id='', mobile='', dev_id='', ver_code='', tick='')

        if '' in (param.app_id, param.mobile, param.dev_id, param.ver_code, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 防止flood攻击，通过app_id 访问时间判断 ---------------------------
        app_id = param.app_id
        now_tick = int(time.time())

        r2 = db.app_device.find_one_and_update(
            {'app_id':app_id},
            {'$set':{'last_tick':now_tick}},
            {'last_tick':1}
        )
        if r2 and now_tick-r2.get('last_tick',0)<3: # n秒内多次login
            env_info = web.ctx.get('environ')
            print 'Warning flood:', app_id, now_tick-r2.get('last_tick',0), env_info.get('REMOTE_ADDR')#, agent
            raise web.notfound()

        #------------------------------------------------------------

        return self.user_forgot(param)

    @staticmethod
    def user_forgot(param):
        number = param.mobile.strip()
        if len(number)<11 or (not number.isdigit()):
            return json.dumps({'ret' : -3, 'msg' : '手机号码格式错误'})

        if number in app_helper.BLOCK_LIST:
            return json.dumps({'ret' : -3, 'msg' : '手机号码错误'})

        # 随机码
        rand = app_helper.my_rand(base=1)
        register = False

        # 检查用户是否已注册
        db_user = db.app_user.find_one({'uname':number})
        if db_user==None:
            # 未注册，新建用户记录
            return json.dumps({'ret' : -5, 'msg' : '手机号码未注册'})
        else:
            # 更新app_id
            userid = db_user['userid']
            db.app_user.update_one({'userid':db_user['userid']},{'$set':{
                'app_id'      : param.app_id,
                'last_status' : int(time.time()),
            }})


        # 生成 session ------------------
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = 'f6102bff8451236b8ca1'
        session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
        session_id = session_id.hexdigest()

        db.app_sessions.insert_one({
            'session_id' : session_id,
            'userid'     : userid,
            'uname'      : number,
            'login'      : 0,
            'rand'       : rand,
            'ip'         : web.ctx.ip,
            'attime'     : now,
            'type'       : 1,
            'pwd_fail'   : 0,
            'bind'       : 1, # 电话用户本身就认为是绑定的
        })

        # -------------------------------


        #发送短信验证码
        if number not in app_helper.INNER_NUM.keys(): # 内部号码不发短信，2015-12-22, gt
            rr = sms.send_rand(number, rand, register) # 测试不发校验码
            if rr is None:
                return json.dumps({'ret': -11, 'msg': '发送太频繁，稍后再试'}) 

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'session'  : session_id,
            }
        })
