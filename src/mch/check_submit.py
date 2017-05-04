#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper
from libs import object_helper

db = setting.db_web

# 提交审核

url = ('/mch/check_submit')

#  -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')
        user_data=web.input(obj_id='', tpc_id='')
        render = helper.create_render()
        mch_id = helper.get_session_mch_id()
        #print mch_id

        if user_data.obj_id=='' and user_data.tpc_id=='' : 
            return render.info('参数错误！')  

        if user_data.obj_id!='': # 课程
            db_obj=db.obj_store.find_one({'obj_id':user_data.obj_id, 'mch_id':mch_id})
            if db_obj is None:
                return render.info('obj_id参数错误！') 

            object_name = db_obj['obj_name']
        else:
            db_obj=db.topic_store.find_one({'tpc_id':user_data.tpc_id, 'mch_id':mch_id})
            if db_obj is None:
                return render.info('tpc_id参数错误！')  

            object_name = db_obj['tpc_name']

        if db_obj.get('status')=='PASSED':
            return render.info('此课程已审核通过！')
        
        return render.check_submit(helper.get_session_uname(), helper.get_privilege_name(), 
            user_data.obj_id, user_data.tpc_id, object_name, db_obj['title'])

    def POST(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')
        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data=web.input(obj_id='', tpc_id='')

        if user_data.obj_id=='' and user_data.tpc_id=='' : 
            return render.info('参数错误！')  

        if user_data.obj_id!='': # 课程
            db_obj=db.obj_store.find_one({'obj_id':user_data.obj_id, 'mch_id':mch_id})
            if db_obj is None:
                return render.info('obj_id参数错误！')  

            object_helper.obj_change_status(user_data['obj_id'], 'WAIT', '提交审核')

            return render.info('成功提交！', '/mch/obj_store')

        else: # 专辑
            db_obj=db.topic_store.find_one({'tpc_id':user_data.tpc_id, 'mch_id':mch_id})
            if db_obj is None:
                return render.info('tpc_id参数错误！')  

            object_helper.topic_change_status(user_data['tpc_id'], 'WAIT', '提交审核')

            return render.info('成功提交！', '/mch/topic_store')

