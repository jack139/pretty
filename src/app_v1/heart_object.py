#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 收藏
url = ('/app/v1/heart_object')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------
        # 区别课程和专辑
        #if param.object_id[0]=='1': # 1 开头是课程，2 开头是专辑
        #    obj_type = 'course'
        #    r3 = db.obj_store.find_one({'obj_id' : param.object_id})
        #else:
        #    obj_type = 'topic'
        #    r3 = db.topic_store.find_one({'tpc_id' : param.object_id})

        # 只收藏课程
        obj_type = 'course'
        r3 = db.obj_store.find_one({'obj_id' : param.object_id})
        if r3 is None:
            return json.dumps({'ret' : -5, 'msg' : '错误的object_id'})

        r2 = db.heart_info.find_one({'userid':uname['userid'],'obj_id':param.object_id})
        if r2 is None: # 收藏动作
            db.heart_info.insert_one({
                'userid'     : uname['userid'],
                'obj_id'     : param.object_id,
                'obj_type'   : obj_type,
                'heart_time' : app_helper.time_str(),
            })

            status = 1

        else: # 取消收藏
            db.heart_info.delete_one({'userid':uname['userid'],'obj_id':param.object_id})
            status = 0

        ret_data = {
            "object_id" : param.object_id,     # 唯一代码 
            "type"  : 1 if obj_type=='course' else 2,  # 类型： 1 课程, 2 专辑 
            "title" : r3['title'],
            "status" : status,
            "msg" : "收藏成功" if status==1 else "取消收藏成功",
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
