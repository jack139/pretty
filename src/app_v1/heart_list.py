#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的收藏列表
url = ('/app/v1/heart_list')

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
        heart_data = []
        r2 = db.heart_info.find({'userid':uname['userid']})
        for i in r2:
            r3 = db.obj_store.find_one({'obj_id' : i['obj_id']})
            if r3 is None:
                continue
            r4 = db.progress_info.find_one({'userid':uname['userid'],'obj_id':i['obj_id']})
            if r4 is None:
                progress = 0
            else:
                progress = r4['progress']
            heart_data.append({
                "object_id"   : i['obj_id'],
                "title"       : r3['title'],
                "type"        : 1,  # 类型： 1 课程, 2 专辑 
                "object_type" : 1 if r3['media']=='video' else 2,  # 1- 视频   2 － 音频  
                "length"      : r3['length'], # 长度，单位 分钟 
                "progress"    : progress, # 进度百分比，如果是未购买课程，此字段为-1
            })

        ret_data = {
            "heart" : heart_data,
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
