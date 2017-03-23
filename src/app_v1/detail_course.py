#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 课程详情
url = ('/app/v1/detail_course')

# 退出
class handler:
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', sign='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.dev_id, param.ver_code, param.session, param.object_id])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "object_id" : param.object_id,     # 唯一代码 
            "title" : "课程标题",
            "title2" : "课程副标题课程副标题",
            "abstract" : "课程简介正文课程简介正文课程简介正文课程简介正文",
            "speaker_head" : "https://pretty.f8cam.com/static/image/banner/head.png",     # 讲师头像图片url 
            "speaker_audio" : "",     # 讲师音频介绍链接
            "course_video" : "",     # 课程视频链接
            "try_length" : 180,  # 0 - 已购买，不是试听，>0 - 可试听的长度，单位 秒
            "volume" : 10,         # 销量 
            "comment_num" : 101,     # 学员评价总条数 
            "exam_score" : -1,    # 课后测试成绩，-1表示未测试
            "service_tel" : "110",     # 客服电话 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
