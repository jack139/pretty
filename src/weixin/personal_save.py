#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json, urllib
from config import setting
import app_helper

db = setting.db_web

# 修改个人信息
url = ('/wx/personal_save')

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', nickname='',headimage='',image_type='')

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        #--------------------------------------------------

        update_set = {}

        if len(param['nickname'])>0:
            update_set['nickname'] = param['nickname']

        if len(param['headimage'])>0:
            if param['image_type'].upper() not in ('JPG','PNG'):
                return json.dumps({'ret' : -5, 'msg' : 'image_type取值错误'})

            data = urllib.unquote_plus(param['headimage'])
            #print data
            #print len(data)

            # 保存图片
            filename = app_helper.write_image(param['image_type'], data)
            update_set['img_url']=app_helper.image_url(filename) # 图片url

        if len(update_set)>0:
            # 只保存在手机号码账户里 type==1
            db.app_user.update_one({'userid':uname['userid'],'type':1},{'$set':update_set})

        # 获取当前设置
        r4 = app_helper.get_user_detail(uname['userid'])

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'headimage_url' : r4['img_url'],
            }
        })
