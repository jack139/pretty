#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import web
import time
from bson.objectid import ObjectId
from config import setting
#from libs import pos_func
import helper

db = setting.db_web

#  专辑上下架编辑

url = ('/plat/topic_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CATEGORY'):
            raise web.seeother('/')

        render = helper.create_render()
        user_data = web.input()


        # 专辑上架商品
        r2 = db.online_topic_obj.find(sort=[('sort_weight', 1)])
        online_obj = [i['tpc_id'] for i in r2]

        # 可上架的专辑
        all_obj = {}
        r3 = db.topic_store.find({'status':'PASSED'})
        for i in r3:
            all_obj[i['tpc_id']] = {'tpc_name':i['tpc_name'], 'mch_id':i['mch_id'], 'tpc_id':i['tpc_id']}

        # 所有商家
        all_mch = {}
        r4  = db.merchant.find({'available':1})
        for i in r4:
            all_mch[i['mch_id']] = i['mch_name']

        return render.topic_plat_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            online_obj, all_obj, all_mch)


    def POST(self):
        if not helper.logged(helper.PRIV_USER, 'CATEGORY'):
            raise web.seeother('/')
        render = helper.create_render()
        user_data=web.input(online_list='')

        if len(user_data.online_list.strip())>0:
            online_list = user_data.online_list.split(',')
        else:
            online_list = []

        print online_list

        # 记录类目商品上架信息
        db.online_topic_obj.remove({})
        for i, tpc_id in enumerate(online_list):
            r3 = db.topic_store.find_one({'tpc_id':tpc_id},{'status':1})
            available = (1 if r3['status']=='PASSED' else 0) if r3 else 0
            db.online_topic_obj.update_one({'tpc_id':tpc_id},
                {'$set':{'available':available, 'sort_weight':i}}, upsert=True)

        return render.info('成功保存！', '/plat/topic_edit')
