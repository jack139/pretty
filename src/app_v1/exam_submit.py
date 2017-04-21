#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 提交测试答卷
url = ('/app/v1/exam_submit')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id','answer'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', answer='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, 
            param.answer, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        # 用户答案
        user_answer = param.answer.upper().split('|')
        #print user_answer

        r2 = db.obj_store.find_one({'obj_id':param['object_id']})
        if r2 is None:
            return json.dumps({'ret' : -5, 'msg' : 'object_id错误'})

        # 获取正确答案
        db_exam = db.exam_info.find({'obj_id':param['object_id'], 'available':1}, 
            sort=[('exam_id', 1)]
        )

        answer_data = []
        score_data = []
        for i in db_exam:
            answer_data.append(''.join(['ABCDEF'[int(x)] for x in i['correct']]))
            score_data.append(i.get('score',10)) # 默认一题10分

        #print answer_data

        # 比对答案，计算成绩
        total_score = 0
        for i in xrange(0, min(len(user_answer), len(answer_data))):
            one_user_a = sorted(user_answer[i])
            one_correct_a = sorted(answer_data[i])
            if one_user_a==one_correct_a:
                total_score += score_data[i]

        ret_data = {
            "exam_score" : total_score, # 测试成绩
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
