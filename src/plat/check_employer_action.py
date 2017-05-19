#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import web
from config import setting
import helper, app_helper

db = setting.db_web


# 审核店主

url = ('/plat/check_employer_action')


# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_EMPLOYER'):
            raise web.seeother('/')
        user_data=web.input(userid='', action='')
        render = helper.create_render()

        action = user_data['action'].upper()
        if action not in ['PASS', 'NOGO', 'WAIT']:
            return render.info('action参数错误！')  


        r2 = db.app_user.find_one({'userid': user_data['userid'], 'type':1})
        if r2 is None:
            return render.info('userid错误！')  

        update_set = {}
        if action=='PASS':
            update_set['user_role'] = 2
            update_set['user_role_status'] = 'PASS'
        elif action=='NOGO':
            update_set['user_role'] = 0
            update_set['user_role_status'] = 'NOGO'
        else:
            update_set['user_role'] = 3
            update_set['user_role_status'] = 'WAIT'

        db.app_user.update_one({'userid': user_data['userid'], 'type':1}, {'$set':update_set})

        return render.info('成功保存！', '/plat/check_employer')
        