#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time, traceback, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/wx_login')


# 微信登录
class handler: 

    @app_helper.check_sign(['app_id','dev_id','ver_code','tick', 'openid', 'unionid', 'nickname', 'img_url'])
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='', 
            openid='', unionid='', nickname='', img_url='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick, param.openid):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 根据openid检查用户是否存在
        db_user = db.app_user.find_one({'openid':param['openid']})
        if db_user==None:
            # 未注册，新建用户记录, 
            new_set = {
                'userid'   : '', # 用户id，未绑定为空
                'openid'   : param['openid'],
                'unionid'  : param['unionid'],
                'type'     : 2, # 1 电话号码用户, 2 微信app登录用户, 3 微信公众号用户, 4 QQ 用户
                'bind'     : 0, # 1 已绑定,  0 未绑定
                'mice'     : 0, # 1 正常用户, 0 黑名单用户
                'app_id'   : param.app_id,
                'reg_time' : app_helper.time_str(),
                'last_status' : int(time.time()),
                'nickname' : param.nickname,
                'img_url'  : param.img_url,
            }

            # 用户中心注册用户接口
            db.app_user.update_one({'openid':param['openid']},{'$set':new_set},upsert=True)

            register = True
        else:
            # 更新app_id
            db.app_user.update_one({'openid':param['openid']},{'$set':{
                'app_id'      : param['app_id'],
                'unionid'     : param['unionid'], # 更新unionid，预防没有unionid的情况
                'nickname'    : param.nickname,
                'img_url'     : param.img_url,
                'last_status' : int(time.time()),
            }})

            register = False

        userid = db_user['userid'] if db_user else ''
        if_bind = (db_user['bind']==1) if db_user else False
        bound_tel = ''

        # 根据unionid检查是否存在关联用户
        if db_user is None or db_user['bind']==0:
            r2 = db.app_user.find_one({'unionid':param['unionid']})
            if r2: # 说明已有公众号用户
                if r2['bind']==1: # 已绑定, 复制userid
                    userid = r2['userid']
                    if_bind = True
                    db.app_user.update_one({'openid':param['openid']},{'$set':{
                        'userid' : userid,
                        'bind'   : 1,
                        'last_status' : int(time.time()),
                    }})

        # 绑定的电话号码
        user_role = 0  # 店员身份， 如果没绑定就不会有
        if if_bind:
            r3 = db.app_user.find_one({'userid':userid, 'type':1})
            if r3:
                bound_tel = r3['uname']
                user_role = r3.get('user_role',0)

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
            'uname'      : param.openid,
            'login'      : 1,
            'ip'         : web.ctx.ip,
            'attime'     : now,
            'type'       : 2,
            'bind'       : 1 if if_bind else 0,
        })

        print 'if_bind', if_bind, bound_tel
        alert = False
        message = ''

        return json.dumps({'ret': 0, 'data': {
            'session'    : session_id,
            'bound_tel'  : bound_tel,
            'if_bind'    : if_bind,   # True表示已绑定手机号（和bind_enable的用处不一样）
            'alert'      : alert,
            'message'    : message,
            'user_new'   : register, #是否为新用户
            'user_role'  : user_role,
        }})


