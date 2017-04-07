#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper

db = setting.db_web

url = ('/mch/obj_store')


# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'OBJ_STORE'):
            raise web.seeother('/')
        render = helper.create_render()

        skus = []
        db_sku = db.obj_store.find(sort=[('available', -1), ('obj_id', -1)])
        
        return render.obj_store(helper.get_session_uname(), helper.get_privilege_name(), db_sku)
