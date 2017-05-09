#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper

db = setting.db_web

# 专辑管理

url = ('/mch/topic_store')

PAGE_SIZE = 50

# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'TOPIC_STORE'):
            raise web.seeother('/')
        user_data=web.input(page='0')
        render = helper.create_render()
        mch_id = helper.get_session_mch_id()
        #print mch_id

        if not user_data['page'].isdigit():
            return render.info('参数错误！')  

        # 分页获取数据
        db_sku = db.topic_store.find({'mch_id':mch_id}, 
            sort=[('obj_id', -1)],
            limit=PAGE_SIZE,
            skip=int(user_data['page'])*PAGE_SIZE
        )

        sku_data = []
        for x in db_sku:
            one = {
                'tpc_id'   : x['tpc_id'],
                'tpc_name' : x['tpc_name'],
                'title'    : x['title'],
                'obj_count' : 0,
                'note'     : x['note'],
                'status'   : x.get('status','SAVED'),
            }
            r2 = db.obj_store.find({'obj_type':'topic', 'tpc_id':x['tpc_id']})
            one['obj_count'] = r2.count()
            sku_data.append(one)

        num = db_sku.count()
        if num%PAGE_SIZE>0:
            num = num / PAGE_SIZE + 1
        else:
            num = num / PAGE_SIZE
        
        return render.topic_store(helper.get_session_uname(), helper.get_privilege_name(), sku_data,
            range(0, num), helper.OBJ_STATUS)
