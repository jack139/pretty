#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 我的课程列表
url = ('/app/v1/list_my_course')

# 退出
class handler: 
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', page_size='', page_index='', sign='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.session, param.page_size, param.page_index, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.dev_id, param.ver_code, param.session,
            param.page_size, param.page_index])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "course" : [
                {
                    "object_id" : "200001",  # 内部唯一标识 
                    "title" : "课程标题",
                    "title2" : "课程副标题课程副标题课程副标题",
                    "speaker" : "讲师名",
                    "type" : 1,  # 1- 视频   2 － 音频  
                    "image" : "https://pretty.f8cam.com/static/image/banner/course.png",  # 课程主图 
                    "length" : 5,  # 长度，单位：分钟 
                    "progress" : 50,  # 课程进度百分比，0表示未上课，100表示已上课 
                    "exam_score" : -1,    # 课后测试成绩，-1表示未测试
                },
                {
                    "object_id" : "200002",  # 内部唯一标识 
                    "title" : "课程标题2",
                    "title2" : "课程副标题课程副标题课程副标题",
                    "speaker" : "讲师名",
                    "type" : 2,  # 1- 视频   2 － 音频  
                    "image" : "https://pretty.f8cam.com/static/image/banner/course.png",  # 课程主图 
                    "length" : 15,  # 长度，单位：分钟 
                    "progress" : 70,  # 课程进度百分比，0表示未上课，100表示已上课 
                    "exam_score" : 80,    # 课后测试成绩，-1表示未测试
                },
            ],
            "total" : 2, # 返回的课程数量，小于 page_size说明到末尾 
            "page_size" : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
