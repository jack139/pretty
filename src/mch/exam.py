#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper

db = setting.db_web

url = ('/mch/exam')

PAGE_SIZE = 50

# 课程测试题
# -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')
        user_data=web.input(page='0', obj_id='')
        render = helper.create_render()
        mch_id = helper.get_session_mch_id()
        #print mch_id

        if not user_data['page'].isdigit():
            return render.info('参数错误！')  

        if user_data['obj_id']=='':
            return render.info('obj_id参数错误！')  

        db_sku = db.exam_info.find({'obj_id':user_data['obj_id'],'mch_id':mch_id}, 
            sort=[('available', -1), ('exam_id', 1)],
            limit=PAGE_SIZE,
            skip=int(user_data['page'])*PAGE_SIZE
        )

        sku_data = []
        for x in db_sku:
            one = {
                'exam_id'  : x['exam_id'],
                'question' : x['question'],
                'available': x['available'],
                'mch_id'   : x['mch_id'],
            }
            sku_data.append(one)

        num = db_sku.count()
        if num%PAGE_SIZE>0:
            num = num / PAGE_SIZE + 1
        else:
            num = num / PAGE_SIZE
        
        return render.exam(helper.get_session_uname(), helper.get_privilege_name(), sku_data,
            range(0, num), user_data['obj_id'])
