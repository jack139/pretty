#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, re
from bson.objectid import ObjectId
from config import setting
import helper
from libs import city_code

db = setting.db_web

url = ('/online/batch_list')

# - 批量列出dispatch和onroad订单
class handler: 
    def GET(self):
        if helper.logged(helper.PRIV_USER,'BATCH_JOB'):
            render = helper.create_render()
            user_data=web.input(status='', sheng='', province_id='', ret_type='table')

            # 统计线上订单
            condition = {
                'status' : user_data['status'],
                #'type'   : {'$in': ['TUAN', 'SINGLE']}, # 目前只拼团用
                'province_id' : user_data['province_id'],
            }

            db_sale2 = db.order_app.find(condition, {
                'order_id'  : 1,
                'paid_time' : 1,
                'cart'      : 1,
                'type'      : 1,
                'status'    : 1,
                'address'   : 1,
                'due'       : 1,
            })

            skus=[]
            title=''
            for i in db_sale2:
                # 地址省份
                county_name,_,_ = city_code.county_id_to_city_name(i['address'][8])

                skus.append({
                    'order_id' : i['order_id'],
                    'cart' : i['cart'],
                    'status' : helper.ORDER_STATUS['APP'][i['status']],
                    'address' : i['address'],
                    'county_name' : county_name
                })

            if user_data.ret_type=='table':
                return render.batch_list(helper.get_session_uname(), helper.get_privilege_name(), 
                    skus, len(skus), user_data['status'], user_data['province_id'], user_data['sheng'])
            else:
                # 返回csv格式文本
                ret_txt=u'订单状态,订单编号,商品清单,省,市,区县,收货姓名,收货电话,收货地址\n'
                for i in skus:
                    line_txt = [
                        i['status'].decode('utf-8'),
                        i['order_id'],
                        u';'.join(['%s[%s]*%d'%(x['product_id'], x['title'], x['num2']) for x in i['cart']]),
                        county_name,
                        i['address'][1],
                        i['address'][2],
                        i['address'][3],
                    ]
                    ret_txt = ret_txt + u','.join(line_txt) + u'\n'
                web.header('Content-Type', 'text/csv')
                web.header('Content-Disposition', 'attachment; filename="%s.csv"'%user_data['status'])
                return ret_txt

        else:
            raise web.seeother('/')


