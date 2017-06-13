#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 专辑详情
url = ('/wx/detail_topic')

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', object_id='')

        if param.object_id=='':
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        #--------------------------------------------------

        r2 = db.topic_store.find_one({
            'tpc_id' : param.object_id, 
        })
        if r2 is None:
            return json.dumps({'ret' : -5, 'msg' : '错误的object_id'})


        r3 = db.obj_store.find({
            'obj_type' : 'topic',
            'tpc_id' : param.object_id, 
        })

        # 专辑内课程数据
        course_data = []
        for i in r3:
            if len(i['image'])>0: # 取第1张图
                image_url = app_helper.image_url(i['image'][0])
            else:
                image_url = ''
            course_data.append({
                "object_id" : i['obj_id'],  # 内部唯一标识 
                "title"     : i['title'],
                "title2"    : i['title2'],
                "speaker"   : i['speaker'],
                "type"      : 1 if i['media']=='video' else 2,  # 1- 视频   2 － 音频  
                "image"     : image_url,  # 课程主图 
                "length"    : i['length'],  # 长度，单位：秒 
                "price"     : i['price'],  # 价格，整数，单位：分 
                "volume"    : r2.get('volume',0), #i['volume'],  # 销量，整数 (专辑课程销量与专辑销量相同？)
            })

        # 取专辑图片
        if len(r2['image'])>0: # 取第1张图
            image_url = app_helper.image_url(r2['image'][0])
        else:
            image_url = ''

        # 返回数据
        ret_data = {
            "object_id"   : param.object_id,     # 唯一代码 
            "title"       : r2['title'],
            "title2"      : r2['title2'],
            "abstract"    : r2['description'],
            "topic_image" : image_url,     # 专辑图片url 
            "booked_num"  : r2.get('volume',0),  # 订阅人数， 销量
            "course"      : course_data,
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
