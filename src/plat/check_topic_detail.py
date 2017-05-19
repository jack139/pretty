#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import web
from config import setting
from libs import object_helper
import helper

db = setting.db_web


# 审核专辑内课程

url = ('/plat/check_topic_detail')

PAGE_SIZE = 50

# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_OBJ'):
            raise web.seeother('/')
        user_data=web.input(page='0', tpc_id='', action='VIEW')
        render = helper.create_render()

        if not user_data['page'].isdigit():
            return render.info('参数错误！')  

        if user_data['tpc_id']=='':
            return render.info('参数错误！')  

        db_tpc = db.topic_store.find_one({'tpc_id':user_data['tpc_id']})
        if db_tpc is None:
            return render.info('专辑信息未找到！')  

        db_sku = db.obj_store.find({'obj_type':'topic', 'tpc_id':user_data['tpc_id']}, # 专辑内课程
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
        
        return render.check_topic_detail(helper.get_session_uname(), helper.get_privilege_name(), sku_data,
            range(0, num), helper.OBJ_STATUS, db_tpc, user_data.action)


    def POST(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_OBJ'):
            raise web.seeother('/')
        render = helper.create_render()
        user_data=web.input(tpc_id='', status='')

        if user_data.tpc_id=='':
            return render.info('参数错误！')  

        if user_data.status=='':
            return render.info('请选择审核结果！')

        tpc_id = user_data['tpc_id']

        message = '审核通过' if user_data['status']=='PASSED' else '审核被拒绝'

        # 专辑课程，需要将专辑状态设置为已保存
        object_helper.topic_change_status(tpc_id, user_data['status'],message,user_data['check_comment'])

        return render.info('成功保存！', '/plat/check_topic')
