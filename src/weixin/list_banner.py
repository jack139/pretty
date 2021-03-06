#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/wx/list_banner')

# 获取轮播图
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
        now_tick = int(time.time())
        
        # 拉取符合条件的banner, 时间区间，是否可用
        r2 = db.banner_info.find({
            'available' : 1,
            '$and' : [{'start_tick':{'$lt':now_tick}},{'expire_tick':{'$gt':now_tick}}],
        }, sort=[('sort_weight',1)])

        banner_data = []
        for i in r2:
            banner_data.append({
                'image' : app_helper.image_url(i['image']),
                'click' : i['click_url'],
            })

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'banner' : banner_data,
            }
        })
