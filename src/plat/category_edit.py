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

# 类目信息编辑

url = ('/plat/category_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CATEGORY'):
            raise web.seeother('/')

        render = helper.create_render()
        user_data = web.input(cate_id='')

        cate_data = { 'cate_id' : 'n/a'}

        if user_data.cate_id != '': 
            db_obj=db.category_info.find_one({'cate_id':user_data.cate_id})
            if db_obj!=None:
                # 已存在的obj
                cate_data = db_obj

        return render.category_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            cate_data)


    def POST(self):
        if not helper.logged(helper.PRIV_USER, 'CATEGORY'):
            raise web.seeother('/')
        render = helper.create_render()
        user_data=web.input(cate_id='',title='')

        if user_data.title.strip()=='':
            return render.info('类目名不能为空！')  

        if user_data.start_time.strip()=='' or user_data.expire_time.strip()=='':
            return render.info('起始时间不能为空！')  

        if user_data['cate_id']=='n/a': # 新建
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'pk_count' : 1}},
                {'pk_count' : 1}
            )
            cate_id = 'c%07d' % db_pk['pk_count']
            message = '新建'
        else:
            cate_id = user_data['cate_id']
            message = '修改'

        try:
            update_set={
                'cate_id'     : cate_id,
                'title'       : user_data['title'],
                'sort_weight' : int(user_data['sort_weight']),
                'available'   : int(user_data['available']),
                'last_tick'   : int(time.time()),  # 更新时间戳
                'start_time'  : user_data['start_time'],
                'expire_time' : user_data['expire_time'],
                'start_tick'  : int(time.mktime(time.strptime(user_data['start_time'],'%Y-%m-%d %H:%M'))),
                'expire_tick'  : int(time.mktime(time.strptime(user_data['expire_time'],'%Y-%m-%d %H:%M'))),
            }
        except ValueError:
            return render.info('请在相应字段输入数字！')

        db.category_info.update_one({'cate_id':cate_id}, {
            '$set'  : update_set,
            '$push' : {
                'history' : (helper.time_str(), helper.get_session_uname(), message), 
            }  # 纪录操作历史
        }, upsert=True)

        return render.info('成功保存！', '/plat/category')
