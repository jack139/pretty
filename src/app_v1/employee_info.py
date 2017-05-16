#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 修改店员信息
url = ('/app/v1/employee_info')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session',
        'shop_name','real_name','shop_nickname','contact_info'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', tick='',
            shop_name='',real_name='',shop_nickname='',contact_info='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 4个信息字段必须填写
        if '' in (param.shop_name.strip(), param.real_name.strip(), 
            param.shop_nickname.strip(), param.contact_info.strip()):
            return json.dumps({'ret' : -3, 'msg' : '必填参数不能为空'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        # 只保存在手机号码账户里 type==1
        db.app_user.update_one({'userid':uname['userid'],'type':1},{'$set':{ 
            'vip_shopname' : param['shop_name'], 
            'vip_realname' : param['real_name'], 
            'vip_nickname' : param['shop_nickname'],
            'vip_contact'  : param['contact_info'],
            'user_role'    : 1, # 店员身份
        }})

        # 返回
        return json.dumps({
            'ret'  : 0,
        })
