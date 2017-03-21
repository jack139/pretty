#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
from bson.objectid import ObjectId
from config import setting
import helper
from libs import city_code

db = setting.db_web

url = ('/report/report1')

# - 线上订单 －－－－－－－－－－－
class handler:        #class PosReport:
    def GET(self):
        if helper.logged(helper.PRIV_USER,'REPORT_REPORT1'):
            render = helper.create_render()
            user_data=web.input(start_date='', shop='__ALL__', ret_type='table')
            
            if user_data['start_date']=='':
                return render.report_report1(helper.get_session_uname(), helper.get_privilege_name())

            # 起至时间
            begin_date = '%s 00:00:00' % user_data['start_date']
            end_date = '%s 23:59:59' % user_data['start_date']

            condition = {
                'status' : {'$nin':['CANCEL','TIMEOUT','DUE','FAIL','REFUND','PREPAID']},
                '$and'   : [{'paid_time' : {'$gt' : begin_date}},
                        {'paid_time' : {'$lt' : end_date}}],
            }

            # 统计线下订单
            db_sale = db.order_app.find(condition, 
                {'order_id':1,'shop':1,'paid_time':1,'uname':1,'due':1,'address':1,'first_disc':1,'status':1})

            print db_sale.count()

            orders = []
            app_cnt = 0
            app_new = 0
            app_money = 0.0
            wx_cnt = 0
            wx_new = 0
            wx_money = 0.0
            
            new_unames = {}

            for i in db_sale:
                new_user = 0

                if not new_unames.has_key(i['uname']):
                    db_user = db.app_user.find_one({'$or' : [ 
                        {'uname':i['uname']},{'openid':i['uname']}  # 2015-10-25
                    ]}, {'reg_time':1})

                    if db_user!=None and db_user['reg_time']>=begin_date and db_user['reg_time']<=end_date:
                        new_unames[i['uname']]=1
                    else:
                        new_unames[i['uname']]=0
                else:
                    print '命中缓存'

                new_user = new_unames[i['uname']]


                if len(i['uname'])>15:
                    wx_cnt += 1
                    wx_new += new_user
                    wx_money += float(i['due'])
                else:
                    app_cnt += 1
                    app_new += new_user
                    app_money += float(i['due'])

                # 地址省份
                county_name,_,_ = city_code.county_id_to_city_name(i['address'][8])

                orders.append((
                    helper.ORDER_STATUS['APP'][i['status']], # 0
                    i['order_id'], # 1
                    i['paid_time'], # 2
                    u'微信' if len(i['uname'])>15 else i['uname'], # 3
                    i['due'], # 4
                    county_name, # 5
                    i['address'][1], # 6
                    i['address'][2], # 7
                    i['address'][3], # 8
                    str(new_user), # 9
                ))


            if user_data.ret_type=='table':
                return render.report_report1_r(helper.get_session_uname(), helper.get_privilege_name(), 
                    orders, user_data.start_date,
                    (app_cnt, wx_cnt), (app_new, wx_new),(app_money, wx_money),
                    user_data['start_date']
                )
            else:
                # 返回csv格式文本
                ret_txt=u'订单状态,订单编号,付款时间,下单手机号,付款金额,省,市,区县,收货姓名,收货电话,收货地址,是否新客'+'\n'
                for i in orders:
                    ret_txt = ret_txt + ','.join(i) + u'\n'
                web.header('Content-Type', 'text/csv')
                web.header('Content-Disposition', 'attachment; filename="report1_%s.csv"'%user_data['start_date'])
                return ret_txt

        else:
            raise web.seeother('/')


