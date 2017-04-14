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

url = ('/mch/topic_store_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'TOPIC_STORE'):
            raise web.seeother('/')

        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data = web.input(tpc_id='')

        obj_data = { 'tpc_id' : 'n/a'}

        if user_data.tpc_id != '': 
            db_obj=db.topic_store.find_one({'tpc_id':user_data.tpc_id, 'mch_id':mch_id})
            if db_obj!=None:
                # 已存在的obj
                obj_data = db_obj

        return render.topic_store_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            obj_data)


    def POST(self):
        if not helper.logged(helper.PRIV_MCH, 'TOPIC_STORE'):
            raise web.seeother('/')
        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data=web.input(tpc_id='')

        if user_data.tpc_name.strip()=='':
            return render.info('品名不能为空！')  


        if user_data['tpc_id']=='n/a': # 新建
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'sa_count' : 1}},
                {'pk_count' : 1}
            )
            tpc_id = '2%07d' % db_pk['pk_count']
            message = '新建'
        else:
            tpc_id = user_data['tpc_id']
            message = '修改'

        try:
            update_set={
                'tpc_id'      : tpc_id,
                'tpc_name'    : user_data['tpc_name'],
                #'list_in_app' : int(user_data['list_in_app']), # 在上架管理里设置
                'title'       : user_data['title'],
                'title2'      : user_data['title2'],
                'description' : user_data['description'],
                'sort_weight' : int(user_data['sort_weight']),
                'note'        : user_data['note'],
                'available'   : int(user_data['available']),
                'last_tick'   : int(time.time()),  # 更新时间戳
                'image'       : user_data['image'].split(','), # 图片
            }
        except ValueError:
            return render.info('请在相应字段输入数字！')

        db.topic_store.update_one({'tpc_id':tpc_id, 'mch_id':mch_id}, {
            '$set'  : update_set,
            '$push' : {
                'history' : (helper.time_str(), helper.get_session_uname(), message), 
            }  # 纪录操作历史
        }, upsert=True)

        return render.info('成功保存！', '/mch/topic_store')
