#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import web
import time
from bson.objectid import ObjectId
from config import setting
from libs import object_helper
import helper

db = setting.db_web

# 审核课程

url = ('/plat/check_obj_detail')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_OBJ'):
            raise web.seeother('/')

        render = helper.create_render()
        user_data = web.input(obj_id='', action='VIEW')

        if user_data.obj_id == '': 
            return render.info('参数错误！')  

        db_obj=db.obj_store.find_one({'obj_id':user_data.obj_id})
        if db_obj is None:
            return render.info('未找到课程信息！')  

        tpc_name = ''
        if db_obj['obj_type']=='topic': # 专辑课程获取专辑名称
            db_topic = db.topic_store.find_one({'tpc_id':db_obj['tpc_id']})
            if db_topic:
                tpc_name = db_topic['tpc_name']

        return render.check_obj_detail(helper.get_session_uname(), helper.get_privilege_name(), 
            db_obj, tpc_name, user_data.action)


    def POST(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_OBJ'):
            raise web.seeother('/')
        render = helper.create_render()
        user_data=web.input(obj_id='', status='')

        if user_data.obj_id=='':
            return render.info('参数错误！')  

        if user_data.status=='':
            return render.info('请选择审核结果！')

        obj_id = user_data['obj_id']

        update_set={
            'check_comment' : user_data['check_comment'],
            'status'        : user_data['status'], 
        }

        message = '审核通过' if user_data['status']=='PASSED' else '审核被拒绝'

        object_helper.obj_change_status(obj_id, user_data['status'], message, user_data['check_comment'])

        return render.info('成功保存！', '/plat/check_obj')
