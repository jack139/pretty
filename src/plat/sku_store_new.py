#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time
from bson.objectid import ObjectId
from config import setting
from libs import pos_func
import helper

db = setting.db_web

url = ('/plat/sku_store_new')

class handler:        # PlatSkuStoreNew
    def GET(self):
        if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
            render = helper.create_render()

            return render.sku_store_new(helper.get_session_uname(), helper.get_privilege_name(), 
                helper.CATEGORY)
        else:
            raise web.seeother('/')

    def POST(self):
        if helper.logged(helper.PRIV_USER,'PLAT_SKU_STORE'):
            render = helper.create_render()
            user_data=web.input(sku_name='', image='', category='')

            if user_data.sku_name=='':
                return render.info('品名不能为空！')  

            if user_data.category=='':
                return render.info('请选择类目！')  

            # 取得sku计数
            db_pk = db.user.find_one_and_update(
                {'uname'    : 'settings'},
                {'$inc'     : {'pk_count' : 1}},
                {'pk_count' : 1}
            )

            product_id = '1%07d' % db_pk['pk_count']

            update_set = {
                'product_id'    : product_id,
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
                'limit_xm'      : int(user_data['limit_xm']),
                'limit_by_id'   : int(user_data['limit_by_id']),
                'sort_weight'   : int(user_data['sort_weight']),
                'hide_after_0'  : int(user_data['hide_after_0']), # 售完隐藏
                'volume'        : int(user_data['volume']),
                'stock'         : int(user_data['stock']),
                #'promote'       : int(user_data['promote']),
                #'image'         : user_data['image'].split(','),

                'last_tick'     : int(time.time()),  # 上架时间戳
                
                'history'       : [(helper.time_str(), helper.get_session_uname(), '新建')], # 纪录操作历史
            }

            # 判断上传图片的大小和格式
            image_list = user_data['image'].split(',')
            #if len(user_data['image'])>0 and len(image_list)>0:
            #    data = pos_func.image_limit(image_list, 'base_sku')
            #    if data['status'] != 0:
            #        return render.info(data['msg'])
            update_set['image'] = image_list

            db.sku_store.insert_one(update_set)

            return render.info('成功保存！','/plat/sku_store')
        else:
            raise web.seeother('/')
