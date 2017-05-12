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
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session',
        'category','pic1','pic1_type','pic2','pic2_type'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='',
            category='', pic1='', pic1_type='', pic2='', pic2_type='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick, 
            param.category, param.pic1, param.pic1_type):
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

        if param['pic2_type'].upper() not in ('JPG','PNG',''):
            return json.dumps({'ret' : -6, 'msg' : '无效的图片类型取值'})

        if len(param['pic2'])>0 and param['pic2_type']=='':
            return json.dumps({'ret' : -6, 'msg' : '无效的图片类型取值'})

        # 保存图片
        pic1_filename = app_helper.write_image(param['pic1_type'], urllib.unquote_plus(param['pic1']))

        if len(param['pic2'])>0:
            pic2_filename = app_helper.write_image(param['pic2_type'], urllib.unquote_plus(param['pic2']))
        else:
            pic2_filename = None

        # 更新数据
        update_set = {}
        if param['category'].upper()=='LICENCE':
            update_set['upload_licence'] = pic1_filename
        else:
            update_set['shop_pic'] = [pic1_filename]
            if pic2_filename is not None:
                update_set['shop_pic'].append(pic2_filename)

        if len(update_set)>0:
            # 只保存在手机号码账户里 type==1
            db.app_user.update_one({'userid':uname['userid'],'type':1},{'$set':update_set})

        # 准备返回值
        ret_data = {
            "pic1_url"  : app_helper.image_url(pic1_filename),
            "pic2_url"  : '',
        }
        if pic2_filename is not None:
            ret_data['pic2_url']=app_helper.image_url(pic2_filename)

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
