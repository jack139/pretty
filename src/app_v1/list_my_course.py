#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的课程列表
url = ('/app/v1/list_my_course')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','page_size','page_index'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', page_size='', page_index='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.page_size,
            param.page_index, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        # 取指定区间的
        start_pos = int(param.page_size)*int(param.page_index)
        end_pos = start_pos + int(param.page_size)

        r2 = db.user_property.find({'userid':uname['userid'], 'status':'paid', 'obj_type':'course'},
            sort=[('_id',1)], # 按时间倒序
            skip=int(param.page_size)*int(param.page_index),
            limit=int(param.page_size)
        )

        course_data = []

        for i in r2:
            r3 = db.obj_store.find_one({'obj_id':i['obj_id']})
            if r3 is None:
                continue

            if len(r3['image'])>0: # 取第1张图
                image_url = app_helper.image_url(r3['image'][0])
            else:
                image_url = ''

            # 已授权店员数，只统计本店主的店员数
            auth_num = db.employee_auth.find({'owner_userid':uname['userid'],'object_list':r3['obj_id']}).count()

            # 测试成绩
            r5 = db.test_info.find_one({'userid':uname['userid'], 'obj_id':r3['obj_id']})
            score = r5['score'] if r5 else -1

            # 完成进度
            r6 = db.progress_info.find_one({'userid':uname['userid'], 'obj_id':r3['obj_id']})
            progress = r6['progress'] if r6 else 0

            course_data.append(
                {
                    "object_id"  : r3['obj_id'],  # 内部唯一标识 
                    "title"      : r3['title'],
                    "title2"     : r3['title2'],
                    "speaker"    : r3['speaker'],
                    "type"       : 1 if r3['media']=='video' else 2,  # 1- 视频   2 － 音频  
                    "image"      : image_url,  # 课程主图 
                    "length"     : r3['length'],  # 长度，单位：分钟 
                    "progress"   : progress,  # 课程进度百分比，0表示未上课，100表示已上课 
                    "exam_score" : score,    # 课后测试成绩，-1表示未测试  
                    "auth_num"   : auth_num, # 已授权店员数 ,
                }
            )

        ret_data = {
            "course"     : course_data,
            "total"      : len(course_data), # 返回的课程数量，小于 page_size说明到末尾 
            "page_size"  : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
