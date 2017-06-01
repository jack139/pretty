#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 获取学员评价
url = ('/app/v1/comment_info')


class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id','page_size','page_index'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', 
            page_size='', page_index='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, 
            param.page_size, param.page_index, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        r2 = db.obj_store.find_one({'obj_id' : param.object_id})
        if r2 is None:
            return json.dumps({'ret' : -5, 'msg' : '错误的object_id'})

        r3 = db.comment_info.find({'obj_id':param.object_id},
            sort=[('last_time',-1)], # 按时间倒序
            skip=int(param.page_size)*int(param.page_index),
            limit=int(param.page_size)
        )

        comment_data = []
        for i in r3:
            r4 = app_helper.get_user_detail(i['userid'])
            comment_data.append({
                "name"  : r4['nickname'],
                "image" : r4['img_url'], # 头像 
                "star"  : i['star'],  # 评的星级 
                "time"  : i['last_time'], 
                "comment"  : i['comment'], 
            })

        ret_data = {
            "comment"    : comment_data,
            "total"      : len(comment_data), # 返回的课程数量，小于 page_size说明到末尾 
            "page_size"  : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
