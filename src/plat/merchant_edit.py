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

# 商家信息编辑

url = ('/plat/merchant_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'MERCHANT'):
            raise web.seeother('/')

        render = helper.create_render()
        user_data = web.input(mch_id='')

        mch_data = { 'mch_id' : 'n/a'}

        if user_data.mch_id != '': 
            db_obj=db.merchant.find_one({'mch_id':user_data.mch_id})
            if db_obj!=None:
                # 已存在的obj
                mch_data = db_obj

        return render.merchant_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            mch_data)


    def POST(self):
        if not helper.logged(helper.PRIV_USER, 'MERCHANT'):
            raise web.seeother('/')
        render = helper.create_render()
        user_data=web.input(mch_id='',mch_name='')

        if user_data.mch_name.strip()=='':
            return render.info('商家名不能为空！')

        if user_data['mch_id']=='n/a': # 新建
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'pk_count' : 1}},
                {'pk_count' : 1}
            )
            mch_id = '0%07d' % db_pk['pk_count']
            message = '新建'
        else:
            mch_id = user_data['mch_id']
            message = '修改'

        try:
            update_set={
                'mch_id'      : mch_id,
                'mch_name'    : user_data['mch_name'],
                'mch_type'    : user_data['mch_type'],
                'note'        : user_data['note'],
                'available'   : int(user_data['available']),
                'last_tick'   : int(time.time()),  # 更新时间戳
            }
        except ValueError:
            return render.info('请在相应字段输入数字！')

        db.merchant.update_one({'mch_id':mch_id}, {
            '$set'  : update_set,
            '$push' : {
                'history' : (helper.time_str(), helper.get_session_uname(), message), 
            }  # 纪录操作历史
        }, upsert=True)

        return render.info('成功保存！', '/plat/merchant')
