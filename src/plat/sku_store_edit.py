#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import web
import time
from bson.objectid import ObjectId
from config import setting
from libs import pos_func
import helper

db = setting.db_web

url = ('/plat/sku_store_edit')

class handler:

    def GET(self):
        if helper.logged(helper.PRIV_USER, 'PLAT_SKU_STORE'):
            render = helper.create_render()
            user_data = web.input(product_id='')
            if user_data.product_id == '':
                return render.info('错误的参数！')

            sku_const = []

            db_sku=db.sku_store.find_one({'product_id':user_data.product_id})
            if db_sku!=None:
                return render.sku_store_edit(helper.get_session_uname(), helper.get_privilege_name(), 
                    db_sku, helper.CATEGORY)
            else:
                return render.info('错误的参数！')  
        else:
            raise web.seeother('/')

    def POST(self):
        if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
            render = helper.create_render()
            user_data=web.input(product_id='')

            if user_data.product_id=='':
                return render.info('请输入必填的参数！')

            if user_data.sku_name=='':
                return render.info('品名不能为空！')  

            if user_data.category=='':
                return render.info('请选择类目！')  

            # 取得现有 ref_price
            #db_ref = db.sku_store.find_one({'_id':ObjectId(user_data['sku'])}, {'product_id': 1, 'price': 1, 'image': 1})
            #ref_price_change = round(float(user_data['price'])-float(db_ref['price']), 2)

            # sku的图片判断
            #if db_ref.get('image', [''])[0] == '' and len(user_data['image'].strip()) == 0:
            #    return render.info('请上传图片！')

            update_set={
                'product_id'    : user_data['product_id'],
                'sku_name'      : user_data['sku_name'],
                'note'          : user_data['note'],
                'available'     : int(user_data['available']),

                'price'         : '%.2f' % float(user_data['price']),
                'is_onsale'     : int(user_data['is_onsale']),
                'special_price' : '%.2f' % float(user_data['special_price']),

                'category'      : user_data['category'],
                'list_in_app'   : int(user_data['list_in_app']),
                'app_title'     : user_data['app_title'],
                'sub_title'     : user_data['sub_title'],
                'description'   : user_data['description'],
                'sort_weight'   : int(user_data['sort_weight']),
                'limit_xm'      : int(user_data['limit_xm']),
                'limit_by_id'   : int(user_data['limit_by_id']),
                'hide_after_0'  : int(user_data['hide_after_0']), # 售完隐藏
                'volume'        : int(user_data['volume']),
                'stock'         : int(user_data['stock']),
                #'promote'       : int(user_data['promote']),
                #'image'         : user_data['image'].split(','),

                'last_tick'     : int(time.time()),  # 更新时间戳
            }

            # 判断上传图片的大小和格式
            image_list = user_data['image'].split(',')
            if len(user_data['image'])>0 and len(image_list) > 0:
                #data = pos_func.image_limit(image_list, 'base_sku')
                #if data['status'] != 0:
                #    return render.info(data['msg'])
                update_set['image'] = user_data['image'].split(',')

            db.sku_store.update_one({'product_id':user_data['product_id']}, {
                '$set'  : update_set,
                '$push' : {
                    'history' : (helper.time_str(), helper.get_session_uname(), '修改'), 
                }  # 纪录操作历史
            })

            return render.info('成功保存！', '/plat/sku_store')
        else:
            raise web.seeother('/')
