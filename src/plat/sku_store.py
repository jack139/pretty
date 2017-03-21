#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper

db = setting.db_web

url = ('/plat/sku_store')


# SKU -------------------
class handler:  # PlatSkuStore
    def GET(self):
        if helper.logged(helper.PRIV_USER, 'PLAT_SKU_STORE'):
            render = helper.create_render()

            skus = []
            db_sku = db.sku_store.find(sort=[('available', -1), ('product_id', -1)])
            
            for u in db_sku:
                # 准备数据
                skus.append((
                    u['product_id'], # 0
                    u['sku_name'], # 1
                    u['app_title'], # 2 
                    u['price'], # 3
                    u['list_in_app'], # 4
                    u['note'],  # 5
                    u['available'], # 6
                ))
            return render.sku_store(helper.get_session_uname(), helper.get_privilege_name(), skus)
        else:
            raise web.seeother('/')

