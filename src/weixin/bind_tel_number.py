#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper
from libs import sms

db = setting.db_web

url = ('/wx/bind_tel_number')


# 微信手机检查验证码
class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', mobile='')

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        #uname = app_helper.wx_logged(param.session_id)
        #if uname is None:
        #    return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        if param.mobile=='':
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        number = param.mobile.strip()
        if len(number)<11 or (not number.isdigit()):
            return json.dumps({'ret' : -10, 'msg' : '手机号码格式错误'})

        if number in app_helper.BLOCK_LIST:
            return json.dumps({'ret' : -10, 'msg' : '手机号码错误'})

        session = app_helper.get_session(param.session_id)
        if session is None:
            return json.dumps({'ret': -4, 'msg': '无效的session_id'})

        if session.get('userid')!='':
            return json.dumps({'ret': -9, 'msg': '已绑定，不能重复绑定'})

        rand = app_helper.my_rand(base=1)
        db.app_sessions.update_one({'session_id': session['session_id']}, {'$set': {
            'attime': time.time(),
            'rand': rand,
        }})

        if number not in app_helper.INNER_NUM.keys(): # 内部号码不发短信，2015-12-22, gt
            #sms.send_rand(param.mobile, rand, False) # 测试不发校验码
            pass

        return json.dumps({'ret': 0, 'data': {
            'session'     : session['session_id'],
            'if_sms_send' : True,
        }})
