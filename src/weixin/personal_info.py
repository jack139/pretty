#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 个人信息
url = ('/wx/personal_info')

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='')

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        #--------------------------------------------------

        r4 = app_helper.get_user_detail(uname['userid'])

        ret_data = {
            "name"      : r4['nickname'],
            "image"     : r4['img_url'],   # 用户头像 
            "tel"       : r4['mobile'], # 用户注册手机号 
            "user_type" : uname['type'], # 用户类型
            # 店员信息
            "shop_name"     : r4.get('shop_name',''),
            "real_name"     : r4.get('real_name',''),
            "shop_nickname" : r4.get('shop_nickname',''),
            "contact_info"  : r4.get('contact_info',''),
            # 店主信息
            "licence_pic"  : app_helper.image_url(r4['licence_pic']) if r4.get('licence_pic','')!='' else '',
            "shop_pic"  : [app_helper.image_url(x) for x in r4.get('shop_pic',[])],
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
