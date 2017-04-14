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

# 轮播图管理

url = ('/plat/banner_edit')

class handler:

    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'BANNER'):
            raise web.seeother('/')

        render = helper.create_render()
        user_data = web.input(banner_id='')

        banner_data = { 'banner_id' : 'n/a'}

        if user_data.banner_id != '': 
            db_obj=db.banner_info.find_one({'banner_id':user_data.banner_id})
            if db_obj!=None:
                # 已存在的obj
                banner_data = db_obj

        return render.banner_edit(helper.get_session_uname(), helper.get_privilege_name(), 
            banner_data)


    def POST(self):
        if not helper.logged(helper.PRIV_USER, 'BANNER'):
            raise web.seeother('/')
        render = helper.create_render()
        user_data=web.input(banner_id='',banner_name='')

        if user_data.banner_name.strip()=='':
            return render.info('轮播图名称不能为空！')  

        if user_data.start_time.strip()=='' or user_data.expire_time.strip()=='':
            return render.info('起始时间不能为空！')  

        if user_data.image.strip()=='':  # 图片
            return render.info('请上传轮播图片')  

        if user_data['banner_id']=='n/a': # 新建
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'pk_count' : 1}},
                {'pk_count' : 1}
            )
            banner_id = 'b%07d' % db_pk['pk_count']
            message = '新建'
        else:
            banner_id = user_data['banner_id']
            message = '修改'

        try:
            update_set={
                'banner_id'   : banner_id,
                'banner_name' : user_data['banner_name'],
                'sort_weight' : int(user_data['sort_weight']),
                'available'   : int(user_data['available']),
                'last_tick'   : int(time.time()),  # 更新时间戳
                'image'       : user_data['image'].split(',')[0], 
                'click_url'   : user_data['click_url'].strip(),
                'start_time'  : user_data['start_time'],
                'expire_time' : user_data['expire_time'],
                'start_tick'  : int(time.mktime(time.strptime(user_data['start_time'],'%Y-%m-%d %H:%M'))),
                'expire_tick'  : int(time.mktime(time.strptime(user_data['expire_time'],'%Y-%m-%d %H:%M'))),
            }
        except ValueError:
            return render.info('请在相应字段输入数字！')

        db.banner_info.update_one({'banner_id':banner_id}, {
            '$set'  : update_set,
            '$push' : {
                'history' : (helper.time_str(), helper.get_session_uname(), message), 
            }  # 纪录操作历史
        }, upsert=True)

        return render.info('成功保存！', '/plat/banner')
