#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 获取课程测试
url = ('/app/v1/exam_course')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        r2 = db.obj_store.find_one({'obj_id':param['object_id']})
        if r2 is None:
            return json.dumps({'ret' : -5, 'msg' : 'object_id错误'})

        db_exam = db.exam_info.find({'obj_id':param['object_id'], 'available':1}, 
            sort=[('exam_id', 1)]
        )

        exam_data = []
        for i in db_exam:
            option = []
            for j in i['option']:
                if len(j.strip())==0:
                    break
                option.append(j)
            exam_data.append({
                "problem" : i['question'],
                "option" : option,
            })

        ret_data = {
           "title"    : r2['title'],
           "note"     : r2.get('exam_note',''),
           "question" : exam_data, 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
