#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json, urllib
from config import setting
import app_helper

db = setting.db_web

# 店主上传图片
url = ('/app/v1/upload_img')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','category','pic1','pic1_type'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='',
            category='', pic1='', pic1_type='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick, param.category):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        if param['category'].upper() not in ('LICENCE','PHOTO'):
            return json.dumps({'ret' : -5, 'msg' : '无效的category取值'})

        if param['pic1_type'].upper() not in ('JPG','PNG'):
            return json.dumps({'ret' : -6, 'msg' : '无效的图片类型取值'})

        # 保存图片
        if len(param['pic1'].strip())>0:
            pic1_filename = app_helper.write_image(param['pic1_type'], urllib.unquote_plus(param['pic1']))
        else:
            pic1_filename = '' # 删除图片

        # 更新数据
        update_set = {}
        if param['category'].upper()=='LICENCE':
            db.app_user.update_one({'userid':uname['userid'],'type':1},{'$set':{'upload_licence':pic1_filename}})
        else:
            if pic1_filename=='': # 删除已上传的图片
                db.app_user.update_one({'userid':uname['userid'],'type':1},{'$set':{'shop_pic':[]}})
            else:
                db.app_user.update_one({'userid':uname['userid'],'type':1},{'$push':{'shop_pic':pic1_filename}})

        # 准备返回值
        ret_data = {
            "pic1_url"  : app_helper.image_url(pic1_filename) if pic1_filename!='' else pic1_filename,
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
