#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/wx_bind')


# 微信绑定手机
class handler: 

    @app_helper.check_sign(['app_id','dev_id','ver_code','tick', 'session', 'mobile', 'rand'])
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='', session='', mobile='', rand='')

        if '' in (param.app_id, param.number, param.dev_id, param.ver_code, param.tick, 
            param.session, param.mobile, param.rand):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        session = app_helper.get_session(param.session)
        if session is None:
            return json.dumps({'ret': -4, 'msg': '无效的sessionid'})

        print '>>>>>> session rand', session.get('rand'), param.rand
        if session.get('rand') != param.rand:
            return json.dumps({'ret': -8, 'msg': '验证码错误'})

        if session.get('userid')!='':
            return json.dumps({'ret': -9, 'msg': '已绑定，不能重复绑定'})

        openid = session.get('uname')

        r3 = db.app_user.find_one({'openid': openid})
        if r3 is None:
            return json.dumps({'ret': -4, 'msg': 'session错误, 未找到openid'})

        # 检查手机号是否存在
        r2 = db.app_user.find_one({'uname': param.mobile})
        if r2 is None:
            # 手机号不存在，自动注册一个手机用户
            userid = app_helper.gen_new_userid()
            new_set = {
                'userid'   : userid, # 用户id，用于唯一标识
                'uname'    : param.mobile,
                'type'     : 1, # 1 电话号码用户, 2 微信app登录用户, 3 微信公众号用户
                'bind'     : 1, # 1 已绑定,  0 未绑定
                'mice'     : 0, # 1 正常用户, 0 黑名单用户
                'app_id'   : param.app_id,
                'reg_time' : app_helper.time_str(),
                'last_status' : int(time.time()),
            }

            # 用户中心注册用户接口
            db.app_user.update_one({'userid':userid},{'$set':new_set},upsert=True)
        else:
            userid = r2['userid']
            db.app_user.update_one({'uname': param.mobile}, {'$set': {
                'bind' : 1,
                'last_status' : int(time.time()),
            }})

        # 绑定
        if r3['unionid']!='':
            # unionid相同的都绑定
            db.app_user.find_many({'unionid': r3['unionid']}, {'$set': {
                'userid'      : userid,
                'bind'        : 1,
                'last_status' : int(time.time()),
            }})
        else:
            # 只绑定此 openid
            db.app_user.update_one({'openid': openid}, {'$set': {
                'userid'      : userid,
                'bind'        : 1,
                'last_status' : int(time.time()),
            }})

        # 更新session
        db.app_sessions.update_one({'session_id': session['session_id']}, {'$set': {
            'userid' : userid,
            'attime' : time.time(),
        }})

        return json.dumps({'ret': 0, 'data': {
            #'userid'    : userid,
            'sessionid' : param.session,
            'bound_tel' : param.mobile,
        }})

