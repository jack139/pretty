#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import web
import time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/mch/exam_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')

        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data = web.input(obj_id='', exam_id='')

        if user_data.obj_id.strip()=='':
            return render.info('obj_id不能为空！')  

        exam_data = { 'exam_id' : 'n/a'}

        if user_data.exam_id != '': 
            db_exam=db.exam_info.find_one({'exam_id':user_data.exam_id, 'mch_id':mch_id})
            if db_exam!=None:
                # 已存在的obj
                exam_data = db_exam

        return render.exam_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            exam_data, user_data.obj_id)


    def POST(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')
        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data=web.input(exam_id='', obj_id='', correct=[], option=[])

        #print user_data

        if user_data.obj_id.strip()=='':
            return render.info('obj_id不能为空！')  

        if user_data.question.strip()=='':
            return render.info('题目内容不能为空！')  

        if user_data['exam_id']=='n/a': # 新建
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'pk_count' : 1}},
                {'pk_count' : 1}
            )
            exam_id = 'ex%07d' % db_pk['pk_count']
            message = '新建'
        else:
            exam_id = user_data['exam_id']
            message = '修改'

        try:
            update_set={
                'obj_id'    : user_data['obj_id'],
                'question'  : user_data['question'],
                'correct'   : user_data['correct'],
                'option'    : user_data['option'],
                'score'     : int(user_data['score']),
                'available' : int(user_data['available']),
                'last_tick' : int(time.time()),  # 更新时间戳
            }
        except ValueError:
            return render.info('请在相应字段输入数字！')

        db.exam_info.update_one({'exam_id':exam_id, 'mch_id':mch_id}, {
            '$set'  : update_set,
            '$push' : {
                'history' : (helper.time_str(), helper.get_session_uname(), message), 
            }  # 纪录操作历史
        }, upsert=True)

        return render.info('成功保存！', '/mch/exam?obj_id=%s'%user_data['obj_id'])
