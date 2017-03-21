#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from libs import city_code
from config import setting
import helper

db = setting.db_web

url = ('/online/batch_job')

# - 批量处理订单
class handler: 
    def GET(self):
        if helper.logged(helper.PRIV_USER,'BATCH_JOB'):
            render = helper.create_render()
            #user_data=web.input(start_date='', shop='__ALL__')
            
            # 统计线上订单
            condition = {
                'status' : {'$in' : ['PAID','DISPATCH','ONROAD']},
                #'type'   : {'$in' : ['TUAN', 'SINGLE']}, # 只拼团用
            }

            db_sale2 = db.order_app.find(condition, {
                'order_id'  : 1,
                'paid_time' : 1,
                'cart'      : 1,
                'type'      : 1,
                'status'    : 1,
                'address'   : 1,
            })

            skus={}
            for i in db_sale2:
                # 区分省份
                if len(i['address'])>=9:
                    county_name,province_id,_ = city_code.county_id_to_city_name(i['address'][8])
                    sheng = county_name.split(',')[0]
                else:
                    sheng = u'其他'
                    province_id = '-1' # id 未知

                if skus.has_key(sheng):
                    skus[sheng]['num'] += 1
                    skus[sheng]['paid'] += (1 if i['status']=='PAID' else 0)
                    skus[sheng]['dispatch'] += (1 if i['status']=='DISPATCH' else 0)
                    skus[sheng]['onroad'] += (1 if i['status']=='ONROAD' else 0)
                else:
                    skus[sheng]={
                        'province_id' : province_id,
                        'num'      : 1, # 要包含送的
                        'paid'     : 1 if i['status']=='PAID' else 0, # 已付款，待拣货的
                        'dispatch' : 1 if i['status']=='DISPATCH' else 0, # 已付款，待配送
                        'onroad'   : 1 if i['status']=='ONROAD' else 0, # 已付款，配送中
                    }

            total_sum={'paid':0, 'dispatch':0, 'onroad':0}
            for i in skus.keys():
                total_sum['paid'] += skus[i]['paid']
                total_sum['dispatch'] += skus[i]['dispatch']
                total_sum['onroad'] += skus[i]['onroad']

            return render.batch_job(helper.get_session_uname(), helper.get_privilege_name(), 
                skus, total_sum)
        else:
            raise web.seeother('/')


