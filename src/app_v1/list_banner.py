#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/list_banner')

# 获取轮播图（不需要session）
class handler: 
    @app_helper.check_sign(['app_id', 'dev_id', 'ver_code', 'tick'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

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
