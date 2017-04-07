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

url = ('/mch/obj_store_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')

        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data = web.input(obj_id='')

        obj_data = { 'obj_id' : 'n/a'}

        if user_data.obj_id != '': 
            db_obj=db.obj_store.find_one({'obj_id':user_data.obj_id, 'mch_id':mch_id})
            if db_obj!=None:
                # 已存在的obj
                obj_data = db_obj

        return render.obj_store_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            obj_data, helper.CATEGORY)


    def POST(self):
        if not helper.logged(helper.PRIV_MCH, 'OBJ_STORE'):
            raise web.seeother('/')
        mch_id = helper.get_session_mch_id()
        render = helper.create_render()
        user_data=web.input(obj_id='')

        if user_data.obj_name=='':
            return render.info('品名不能为空！')  

        if user_data.cate_id=='':
            return render.info('请选择类目！')  

        if not user_data.has_key('media'):
            return render.info('请选择媒体类型！')


        if user_data['obj_id']=='n/a': # 新建
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'pk_count' : 1}},
                {'pk_count' : 1}
            )
            obj_id = '1%07d' % db_pk['pk_count']
            message = '新建'
        else:
            obj_id = user_data['obj_id']
            message = '修改'

        try:
            update_set={
                'obj_id'      : obj_id,
                'obj_name'    : user_data['obj_name'],
                #'list_in_app' : int(user_data['list_in_app']), # 在上架管理里设置
                'cate_id'     : user_data['cate_id'],
                'title'       : user_data['title'],
                'title2'      : user_data['title2'],
                'speaker'     : user_data['speaker'],
                'description' : user_data['description'],
                'price'       : int(float(user_data['price'])*100), # 单位： 分
                'volume'      : int(user_data['volume']),
                'media'       : user_data['media'],
                'length'      : int(user_data['length']),
                'try_time'    : int(user_data['try_time']),
                'sort_weight' : int(user_data['sort_weight']),
                'note'        : user_data['note'],
                'available'   : int(user_data['available']),
                'last_tick'   : int(time.time()),  # 更新时间戳
            }
        except ValueError:
            return render.info('请在相应字段输入数字！')

        # 判断上传图片的大小和格式
        image_list = user_data['image'].split(',')
        if len(user_data['image'])>0 and len(image_list) > 0:
            update_set['image'] = user_data['image'].split(',')

        db.obj_store.update_one({'obj_id':obj_id, 'mch_id':mch_id}, {
            '$set'  : update_set,
            '$push' : {
                'history' : (helper.time_str(), helper.get_session_uname(), message), 
            }  # 纪录操作历史
        }, upsert=True)

        return render.info('成功保存！', '/mch/obj_store')
