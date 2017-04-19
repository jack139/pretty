#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 提交课程评价
url = ('/app/v1/comment_save')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id','comment','star'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', 
            comment='', star='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, 
            param.star, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if not param.star.isdigit():
            return json.dumps({'ret' : -3, 'msg' : 'star参数必须是数字'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        r2 = db.obj_store.find_one({'obj_id' : param.object_id})
        if r2 is None:
            return json.dumps({'ret' : -5, 'msg' : '错误的object_id'})

        db.comment_info.update_one({
            'userid'    : uname['userid'],
            'obj_id'    : param.object_id,
        },{'$set':{
            'mch_id'    : r2['mch_id'],
            'star'      : int(param.star)%6, # star取值 0-5
            'comment'   : param.comment,
            'last_time' : app_helper.time_str(),
        }}, upsert=True)

        # 返回
        return json.dumps({
            'ret'  : 0,
        })
