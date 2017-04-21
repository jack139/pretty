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

        sku_data = []
        for x in db_sku:
            one = {
                'obj_id'   : x['obj_id'],
                'obj_name' : x['obj_name'],
                'title'    : x['title'],
                'obj_type' : x['obj_type'],
                'price'    : x['price'],
                'tpc_name' : 'n/a',
                'available': x['available'],
                'note'    : x['note'],
            }
            if x['obj_type']=='topic':
                r2 = db.topic_store.find_one({'tpc_id':x['tpc_id']})
                one['tpc_name'] = one['tpc_name'] if r2 is None else r2['tpc_name']
            sku_data.append(one)


        num = db_sku.count()
        if num%PAGE_SIZE>0:
            num = num / PAGE_SIZE + 1
        else:
            num = num / PAGE_SIZE
        
        return render.obj_store(helper.get_session_uname(), helper.get_privilege_name(), sku_data,
            range(0, num))
