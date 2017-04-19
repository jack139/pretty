#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 试听课程列表
url = ('/app/v1/list_try')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','category','page_size','page_index'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', category='', 
            page_size='', page_index='', tick='')

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
        cate_id = param['category'].strip() if param['category'].strip()!='' else app_helper.DEFAULT_CATEGORY

        r2 = db.online_cate_obj.find({
            'cate_id'   : cate_id, 
            'available' : 1,
        }, sort=[('sort_weight', 1)])

        obj_list = [i['obj_id'] for i in r2]

        r3 = db.obj_store.find({
            'obj_id'   : {'$in' : obj_list},
            'try_time' : {'$gt' : 0},
        })

        obj_data = {}
        for i in r3:
            obj_data[i['obj_id']]=i

        # 所有试听数据
        try_obj_list = []
        for i in obj_list:
            if i not in obj_data.keys():
                continue
            try_obj_list.append({
                'object_id' : obj_data[i]['obj_id'], 
                'title'     : obj_data[i]['title'],
                'title2'    : obj_data[i]['title2'],
                'speaker'   : obj_data[i]['speaker'],
                'type'      : 1 if obj_data[i]['media']=='video' else 2,  # 1- 视频   2 － 音频  
                'image'     : [app_helper.image_url(x) for x in obj_data[i]['image']], 
                'length'    : obj_data[i]['length'],  # 长度，单位：秒
                'try_time'  : obj_data[i]['try_time'],  # 试听长度，单位：秒 
            })

        # 取指定区间的
        start_pos = int(param.page_size)*int(param.page_index)
        end_pos = start_pos + int(param.page_size)
        try_obj_list_page = try_obj_list[start_pos:end_pos]


        ret_data = {
            "try" : try_obj_list_page,
            "total" : len(try_obj_list_page), # 返回的课程数量，小于 page_size说明到末尾 
            "page_size" : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        #print ret_data

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
