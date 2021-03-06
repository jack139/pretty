#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 个人信息
url = ('/app/v1/personal_info')

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

        #--------------------------------------------------

        r4 = app_helper.get_user_detail(uname['userid'])

        ret_data = {
            "name"      : r4['nickname'],
            "image"     : r4['img_url'],   # 用户头像 
            "tel"       : r4['mobile'], # 用户注册手机号 
            "user_type" : uname['type'], # 用户类型
            # 店员信息
            "shop_name"     : r4['shop_name'],
            "real_name"     : r4['real_name'],
            "shop_nickname" : r4['shop_nickname'],
            "contact_info"  : r4['contact_info'],
            # 店主信息
            "licence_pic"  : app_helper.image_url(r4['licence_pic']) if r4['licence_pic']!='' else r4['licence_pic'],
            "shop_pic"  : [app_helper.image_url(x) for x in r4['shop_pic']],
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
