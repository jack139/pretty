#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/report/report2')

# - 销货记录 所有门店－－－－－－－－－－－
class handler:        #class PosReport:
    def GET(self):
        if helper.logged(helper.PRIV_USER,'REPORT_REPORT1'):
            render = helper.create_render()
            user_data=web.input(start_date='', shop='__ALL__', ret_type='table')
            
            if user_data['start_date']=='':
                return render.report_report2(helper.get_session_uname(), helper.get_privilege_name())


            # 起至时间
            begin_date = '%s 00:00:00' % user_data['start_date']
            end_date = '%s 23:59:59' % user_data['start_date']

            condition = {
                'status' : 'PAID',
                '$and'   : [{'paid_time' : {'$gt' : begin_date}},
                        {'paid_time' : {'$lt' : end_date}}],
            }

            # 统计线上订单
            condition['status']={'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND']}
            db_sale2 = db.order_app.find(condition, 
                {'order_id':1,'due':1,'total':1,'pay':1,'paid_time':1,'cart':1,'shop':1,'type':1,'status':1,'delivery_fee':1})

            total3 = 0.0
            total4 = 0.0
            count3 = 0
            tuan = 0
            tuan_dark = 0
            skus = {}
            for i in db_sale2:
                for j in i['cart']:
                    if skus.has_key(j['product_id']):
                        skus[j['product_id']]['online']['price'] += float(j['price'])
                        # 要包含送的
                        skus[j['product_id']]['online']['num'] += (float(j['num2'])+float(j.get('numyy','0.00')))
                        skus[j['product_id']]['online']['paid'] += (1 if i['status']=='PAID' else 0)
                        skus[j['product_id']]['online']['dispatch'] += (1 if i['status']=='DISPATCH' else 0)
                        skus[j['product_id']]['online']['onroad'] += (1 if i['status']=='ONROAD' else 0)
                        skus[j['product_id']]['online']['complete'] += (1 if i['status']=='COMPLETE' else 0)
                    else:
                        skus[j['product_id']]={
                            'online' : {
                                'price' : float(j['price']),
                                'num'   : float(j['num2'])+float(j.get('numyy','0.00')), # 要包含送的
                                'paid'  : 1 if i['status']=='PAID' else 0, # 已付款，待拣货的，
                                'dispatch'  : 1 if i['status']=='DISPATCH' else 0, # 已付款，待配送， 
                                'onroad'  : 1 if i['status']=='ONROAD' else 0, # 已付款，配送中，
                                'complete'  : 1 if i['status']=='COMPLETE' else 0, # 已付款，配送完成，
                            },
                            'name'  : j['title'],
                        }

                total3 += float(i['due'])
                total4 += float(i['total'])
                count3 += 1

            if user_data.ret_type=='table':
                return render.report_report2_r(helper.get_session_uname(), helper.get_privilege_name(), 
                    skus, len(skus), 
                    ('', '', '', # 线上暗店
                    '%.2f' % total4, '%.2f' % (total4-total3), '%.2f' % total3), # 线上明店
                    count3,
                    user_data.start_date)
            else:
                # 返回csv格式文本
                ret_txt=u'商品ID,名称,线上数量,线上销售,待拣货,待配送,配送中,配送完成'+'\n'
                for i in skus.keys():
                    line_txt = [
                        i,
                        skus[i]['name'],
                        ('%.0f' % skus[i]['online']['num']),
                        ('%.2f' % skus[i]['online']['price']),
                        ('%.0f' % skus[i]['online']['paid']),
                        ('%.0f' % skus[i]['online']['dispatch']),
                        ('%.0f' % skus[i]['online']['onroad']),
                        ('%.0f' % skus[i]['online']['complete']),
                    ]
                    ret_txt = ret_txt + ','.join(line_txt) + u'\n'
                web.header('Content-Type', 'text/csv')
                web.header('Content-Disposition', 'attachment; filename="report2_%s.csv"'%user_data['start_date'])
                return ret_txt

        else:
            raise web.seeother('/')


