#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper

db = setting.db_web

url = ('/mch/obj_store')

PAGE_SIZE = 50

# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')
        user_data=web.input(page='0')
        render = helper.create_render()
        mch_id = helper.get_session_mch_id()
        #print mch_id

        if not user_data['page'].isdigit():
            return render.info('参数错误！')  

        db_sku = db.obj_store.find({'mch_id':mch_id}, 
            sort=[('available', -1), ('obj_id', -1)],
            limit=PAGE_SIZE,
            skip=int(user_data['page'])*PAGE_SIZE
        )

        num = db_sku.count()
        if num%PAGE_SIZE>0:
            num = num / PAGE_SIZE + 1
        else:
            num = num / PAGE_SIZE
        
        return render.obj_store(helper.get_session_uname(), helper.get_privilege_name(), db_sku,
            range(0, num))
