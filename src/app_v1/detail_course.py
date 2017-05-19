#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 课程详情
url = ('/app/v1/detail_course')

class handler:
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})
        else:
            uname = None

        #--------------------------------------------------

        r3 = db.obj_store.find_one({
            'obj_id' : param.object_id, 
        })
        if r3 is None:
            return json.dumps({'ret' : -5, 'msg' : '错误的object_id'})

        if len(r3['image'])>1: # 取第2张图, 讲师头像
            image_url = app_helper.image_url(r3['image'][1])
        else:
            image_url = ''

        # 评价条数
        r4 = db.comment_info.find({'obj_id':param.object_id}).count()

        # 测试成绩
        r5 = db.test_info.find_one({'userid':uname['userid'], 'obj_id':param.object_id})
        score = r5['score'] if r5 else -1

        ret_data = {
            "object_id"     : param.object_id,     # 唯一代码 
            "title"         : r3['title'],
            "title2"        : r3['title2'],
            "abstract"      : r3['description'],
            "type"          : 1 if r3['media']=='video' else 2,
            "speaker_head"  : image_url,     # 讲师头像图片url 
            "speaker_audio" : '',     # 讲师音频介绍链接, -------------------- 待实现
            "course_video"  : '',     # 课程视频链接 -------------------- 待实现
            "try_length"    : r3['try_time'],  # 0 - 已购买，不是试听，>0 - 可试听的长度，单位 秒
            "volume"        : r3['volume'],         # 销量 

            "comment_num" : r4,     # 学员评价总条数 
            "exam_score"  : score,    # 课后测试成绩，-1表示未测试 
            "service_tel" : app_helper.CS_TEL,
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
