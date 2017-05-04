#!/usr/bin/env python
# -*- coding: utf-8 -*-
# new_sku_store.py
import web
from config import setting
import helper

db = setting.db_web


# 审核课程

url = ('/plat/check_obj')

PAGE_SIZE = 50

# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_OBJ'):
            raise web.seeother('/')
        user_data=web.input(page='0')
        render = helper.create_render()

        if not user_data['page'].isdigit():
            return render.info('参数错误！')  

        db_sku = db.obj_store.find({'obj_type':'course','status':{'$in':['WAIT', 'PASSED', 'DENY']}},  # 只显示精品课程
            sort=[('obj_id', -1)],
            limit=PAGE_SIZE,
            skip=int(user_data['page'])*PAGE_SIZE
        )

        sku_data = []
        for x in db_sku:
            one = {
                'obj_id'   : x['obj_id'],
                'obj_name' : x['obj_name'],
                'title'    : x['title'],
                'price'    : x['price'],
                'note'     : x['note'],
                'status'   : x.get('status','SAVED'),
            }
            sku_data.append(one)

        num = db_sku.count()
        if num%PAGE_SIZE>0:
            num = num / PAGE_SIZE + 1
        else:
            num = num / PAGE_SIZE
        
        return render.check_obj(helper.get_session_uname(), helper.get_privilege_name(), sku_data,
            range(0, num), helper.OBJ_STATUS)
