#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json, urllib
from config import setting
import app_helper

db = setting.db_web

# 修改个人信息
url = ('/app/v1/personal_save')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session',
        'nickname','headimage','image_type'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='',
            nickname='',headimage='',image_type='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

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
