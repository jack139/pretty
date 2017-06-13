#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 课程详情
url = ('/wx/detail_course')

class handler:
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', object_id='')

        if param.object_id == '':
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

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

        if len(r3['image'])>0: # 取第1张图
            image_url_1 = app_helper.image_url(r3['image'][0])
        else:
            image_url_1 = ''

        # 评价条数
        r4 = db.comment_info.find({'obj_id':param.object_id}).count()

        # 是否已购买或已授权, 不需要试听
        can_use = False
        score = -1
        is_heart = 0
        if uname is not None:
            # 检查 是否是已购买
            r6 = db.user_property.find_one({
                'userid' : uname['userid'],
                'obj_id' : param.object_id,
                'status' : 'paid',
            })
            if r6:
                can_use = True
            else:
                # 检查 是否是已授权
                r7 = db.employee_auth.find_one({
                    'employee_userid' : uname['userid'],
                    'object_list'     : param.object_id,
                })
                if r7:
                    can_use = True

            # 测试成绩
            r5 = db.test_info.find_one({'userid':uname['userid'], 'obj_id':param.object_id})
            score = r5['score'] if r5 else -1

            # 检查是否已收藏
            r8 = db.heart_info.find_one({'userid':uname['userid'],'obj_id':param.object_id})
            is_heart = 0 if r8 is None else 1

        # 音频／视频下载链接
        media_url = ''
        if len(r3.get('media_file',''))>0:
            if r3['media']=='audio': # 音频
                media_url = app_helper.audio_url(r3['media_file'])
            elif r3.has_key('transcoded_filename') and (r3['transcoded_filename'] not in ['FAIL','CODING']):
                media_url = app_helper.video_url(r3['transcoded_filename'])

        # 讲师介绍音频
        if len(r3.get('speaker_media',''))>0:
            speaker_url = app_helper.audio_url(r3['speaker_media'])
        else:
            speaker_url = ''

        # 是否有测试题
        exam_cnt = db.exam_info.find({'obj_id':param.object_id, 'available':1}).count()


        # 返回的数据
        ret_data = {
            "object_id"     : param.object_id,     # 唯一代码 
            "title"         : r3['title'],
            "title2"        : r3['title2'],
            "abstract"      : r3['description'],
            "type"          : 1 if r3['media']=='video' else 2,
            "speaker_head"  : image_url,     # 讲师头像图片url 
            "speaker_audio" : speaker_url,     # 讲师音频介绍链接
            "course_video"  : media_url,     # 课程视频链接 
            "try_length"    : 0 if can_use else max(r3['try_time'], 1),  # 0 - 已购买，不是试听，>0 - 可试听的长度，单位 秒
            "volume"        : r3['volume'],         # 销量 

            "comment_num" : r4,     # 学员评价总条数 
            "exam_score"  : score,    # 课后测试成绩，-1表示未测试 
            "service_tel" : app_helper.CS_TEL,

            'speaker'     : r3['speaker'],
            'price'       : r3['price'],  # 价格 单位：分
            'image'       : image_url_1, # 课程主图

            "have_exam"  : 1 if exam_cnt>0 else 0, # 是否有课后测试，2017-06-09
            "is_heart"   : is_heart, # 是否已收藏，2017-06-09
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
