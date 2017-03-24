#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper
from libs import sms
#from libs import settings_helper
#from libs import app_user_helper

db = setting.db_web

url = ('/app/v1/user_login')


# 用户注册／登录
class handler: # Login2:
    @app_helper.check_sign(['app_id','number','dev_id','ver_code','tick'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        #print web.input()
        param = web.input(app_id='', number='', dev_id='', ver_code='', tick='')

        if '' in (param.app_id, param.number, param.dev_id, param.ver_code, param.tick):
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

        return self.user_login(param)

    @staticmethod
    def user_login(param):
        number = param.number.strip()
        if len(number)<11 or (not number.isdigit()):
            return json.dumps({'ret' : -5, 'msg' : '手机号码格式错误'})

        if number in app_helper.BLOCK_LIST:
            return json.dumps({'ret' : -5, 'msg' : '手机号码错误'})

        # 随机码
        rand = app_helper.my_rand(base=1)
        register = False

        # 检查用户是否已注册
        db_user = db.app_user.find_one({'uname':number})
        if db_user==None:
            # 未注册，新建用户记录
            new_set = {
                'uname'    : number,
                'app_id'   : param.app_id,
                'reg_time' : app_helper.time_str(),
                'last_status' : int(time.time()),
                'app_order_num': 0  # 未下单
            }

            # 用户中心注册用户接口
            db.app_user.update_one({'uname':number},{'$set':new_set},upsert=True)

            register = True

        else:

            # 更新app_id
            db.app_user.update_one({'uname':number},{'$set':{'app_id':param.app_id}})


        # 生成 session ------------------
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = 'f6102bff8451236b8ca1'
        session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
        session_id = session_id.hexdigest()

        db.app_sessions.insert_one({
            'session_id' : session_id,
            'uname'      : number,
            'login'      : 0,
            'rand'       : rand,
            'ip'         : web.ctx.ip,
            'attime'     : now,
            'type'       : 'app',
            'pwd_fail'   : 0,
        })

        # -------------------------------


        #发送短信验证码
        if number not in app_helper.INNER_NUM.keys(): # 内部号码不发短信，2015-12-22, gt
            #sms.send_rand(number, rand, register) # 测试不发校验码
            pass

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'session'  : session_id,
                'user_new' : register,
            }
        })
