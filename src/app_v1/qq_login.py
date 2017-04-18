#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time, traceback, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/qq_login')


# QQ登录
class handler: 

    @app_helper.check_sign(['app_id','dev_id','ver_code','tick', 'qqid', 'nickname', 'img_url'])
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='', 
            qqid='', nickname='', img_url='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick, param.qqid):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 根据qqid检查用户是否存在
        db_user = db.app_user.find_one({'qqid':param['qqid']})
        if db_user==None:
            # 未注册，新建用户记录, 
            new_set = {
                'userid'   : '', # 用户id，未绑定为空
                'qqid'   : param['qqid'],
                #'unionid'  : param['unionid'],
                'type'     : 4, # 1 电话号码用户, 2 微信app登录用户, 3 微信公众号用户, 4 QQ用户
                'bind'     : 0, # 1 已绑定,  0 未绑定
                'mice'     : 0, # 1 正常用户, 0 黑名单用户
                'app_id'   : param.app_id,
                'reg_time' : app_helper.time_str(),
                'last_status' : int(time.time()),
            }

            # 用户中心注册用户接口
            db.app_user.update_one({'qqid':param['qqid']},{'$set':new_set},upsert=True)

            register = True
        else:
            # 更新app_id
            db.app_user.update_one({'qqid':param['qqid']},{'$set':{
                'app_id'      : param['app_id'],
                #'unionid'     : param['unionid'], # 更新unionid，预防没有unionid的情况
                'last_status' : int(time.time()),
            }})

            register = False

        userid = db_user['userid'] if db_user else ''
        if_bind = (db_user['bind']==1) if db_user else False
        bound_tel = ''

        # 绑定的电话号码
        if if_bind:
            r3 = db.app_user.find_one({'userid':userid, 'type':1})
            if r3:
                bound_tel = r3['uname']

        # 生成session
        import os
        rand2 = os.urandom(16)
        now = time.time()
        secret_key = 'f6102bff8451236b8ca1'
        session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
        session_id = session_id.hexdigest()

        db.app_sessions.insert_one({
            'session_id' : session_id,
            'userid'     : userid,
            'uname'      : param.qqid,
            'login'      : 1,
            'ip'         : web.ctx.ip,
            'attime'     : now,
            'type'       : 4,
        })

        print 'if_bind', if_bind, bound_tel
        alert = False
        message = ''

        return json.dumps({'ret': 0, 'data': {
            'session_id' : session_id,
            'bound_tel'  : bound_tel,
            'if_bind'    : if_bind,   # True表示已绑定手机号（和bind_enable的用处不一样）
            'alert'      : alert,
            'message'    : message,
            'user_new'   : register, #是否为新用户
        }})


