#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 精品专辑列表
url = ('/app/v1/list_topic')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','page_size','page_index'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', page_size='', page_index='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.page_size, param.page_index, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})
        else:
            uname = None

        #--------------------------------------------------
        r2 = db.online_topic_obj.find({
            'available' : 1,
        }, sort=[('sort_weight', 1)])

        tpc_list = [i['tpc_id'] for i in r2]

        # 取指定区间的
        start_pos = int(param.page_size)*int(param.page_index)
        end_pos = start_pos + int(param.page_size)
        tpc_list_page = tpc_list[start_pos:end_pos]

        r3 = db.topic_store.find({'tpc_id' : {'$in' : tpc_list_page}})

        tpc_data = {}
        for i in r3:
            tpc_data[i['tpc_id']]=i

        # 准备返回数据
        ret_tpc_list = []
        for i in tpc_list_page:
            r4 = db.obj_store.find({'obj_type':'topic','tpc_id':tpc_data[i]['tpc_id']})
            topic_count = r4.count() # 专辑内课程数
            if topic_count>0:
                media = r4[0]['media']
            else:
                media = 'audio' # 默认为音频

            if len(tpc_data[i]['image'])>0: # 取第1张图
                image_url = app_helper.image_url(tpc_data[i]['image'][0])
            else:
                image_url = ''

            ret_tpc_list.append({
                'object_id' : tpc_data[i]['tpc_id'], 
                'title'     : tpc_data[i]['title'],
                'title2'    : tpc_data[i]['title2'],
                'type'      : 1 if media=='video' else 2,  # 1- 视频   2 － 音频  
                'image'     : image_url, 
                'length'    : topic_count,  # 长度，单位：几个课程
            })

        ret_data = {
            "topic" : ret_tpc_list,
            "total" : len(ret_tpc_list), # 返回的课程数量，小于 page_size说明到末尾 
            "page_size" : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
