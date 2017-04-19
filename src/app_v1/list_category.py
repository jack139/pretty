#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/list_category')

# 获取课程分类（不需要session）
class handler: 
    @app_helper.check_sign(['app_id', 'dev_id', 'ver_code', 'tick','session'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='', session='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})
        else:
            uname = None

        #--------------------------------------------------
        now_tick = int(time.time())

        # 拉取符合条件的类目, 时间区间，是否可用
        r2 = db.category_info.find({
            'available' : 1,
            '$and' : [{'start_tick':{'$lt':now_tick}},{'expire_tick':{'$gt':now_tick}}],
        }, sort=[('sort_weight',1)])

        category_data = []
        for i in r2:
            category_data.append({
                'key' : i['cate_id'],
                'title' : i['title'],
            })

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'category' : category_data,
            }
        })
