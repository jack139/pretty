#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time
from config import setting
import helper, app_helper

db = setting.db_web

url = ('/crm')

# crm页面
class handler:
    def GET(self):
        if helper.logged(helper.PRIV_USER,'CRM'):
            render = helper.create_render()
            return render.crm(helper.get_session_uname(), helper.get_privilege_name())
        else:
            raise web.seeother('/')

    def POST(self):
        import re
        if helper.logged(helper.PRIV_USER,'CRM'):
            render = helper.create_render()
            user_data=web.input(cat='', content='')

            if user_data.cat=='' or user_data.content=='':
                return render.info('错误的参数！')

            if user_data.cat=='order_id' and len(user_data.content.strip())==18:
                condi = { 'order_id':user_data.content.strip() }
            elif user_data.cat=='uname' and (len(user_data.content.strip())==11 or len(user_data.content.strip())==28):
                if user_data.content.strip() not in app_helper.BLOCK_LIST:
                    condi = { 'uname':user_data.content.strip() }
                else:
                    return render.info('未查到订单信息。')
            elif user_data.cat=='recv_tel':
                if user_data.content.strip() not in app_helper.BLOCK_LIST:
                    condi = { 'address.2':user_data.content.strip() }
                else:
                    return render.info('未查到订单信息。')
            elif user_data.cat=='tracking_num':
                condi = { 'tracking_num':user_data.content.strip() }
            else:
                condi = {
                    #user_data.cat:{'$in': [re.compile('^.*%s.*' % user_data.content.strip().encode('utf-8'))]},
                    user_data.cat:user_data.content.strip(),
                    #'status':{'$nin':['TIMEOUT']}
                }

            db_todo = db.order_app.find(condi, 
                {'order_id':1,'uname':1,'paid_time':1,'status':1}).sort([('b_time',-1)])
            if db_todo.count()>0:
                return render.report_order(helper.get_session_uname(), helper.get_privilege_name(), 
                    db_todo, helper.ORDER_STATUS)
            else:
                return render.info('未查到订单信息。')
        else:
            raise web.seeother('/')
