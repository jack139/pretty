#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper
from libs import sms

db = setting.db_web

url = ('/app/v1/bind_tel_number')


# 微信手机检查验证码
class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick', 'session', 'mobile'])
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='', session='', mobile='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick, 
            param.session, param.mobile):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        number = param.mobile.strip()
        if len(number)<11 or (not number.isdigit()):
            return json.dumps({'ret' : -10, 'msg' : '手机号码格式错误'})

        if number in app_helper.BLOCK_LIST:
            return json.dumps({'ret' : -10, 'msg' : '手机号码错误'})

        session = app_helper.get_session(param.session)
        if session is None:
            return json.dumps({'ret': -4, 'msg': '无效的sessionid'})

        if session.get('userid')!='':
            return json.dumps({'ret': -9, 'msg': '已绑定，不能重复绑定'})

        rand = app_helper.my_rand(base=1)
        db.app_sessions.update_one({'session_id': session['session_id']}, {'$set': {
            'attime': time.time(),
            'rand': rand,
        }})

        if number not in app_helper.INNER_NUM.keys(): # 内部号码不发短信，2015-12-22, gt
            rr = sms.send_rand(param.mobile, rand, False) # 测试不发校验码
            if rr is None:
                return json.dumps({'ret': -11, 'msg': '发送太频繁，稍后再试'}) 

        return json.dumps({'ret': 0, 'data': {
            'session'     : session['session_id'],
            'if_sms_send' : True,
        }})
