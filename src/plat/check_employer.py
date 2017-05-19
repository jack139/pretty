#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
import web
from config import setting
import helper, app_helper

db = setting.db_web


# 审核店主

url = ('/plat/check_employer')

PAGE_SIZE = 50

# SKU -------------------
class handler:  
    def GET(self):
        if not helper.logged(helper.PRIV_USER, 'CHECK_EMPLOYER'):
            raise web.seeother('/')
        user_data=web.input(page='0')
        render = helper.create_render()

        if not user_data['page'].isdigit():
            return render.info('参数错误！')  

        db_sku = db.app_user.find({'user_role': {'$in' : [2,3]}},  # 只显示店主或申请店主的
            sort=[('user_role', -1)],
            limit=PAGE_SIZE,
            skip=int(user_data['page'])*PAGE_SIZE
        )

        sku_data = []
        for x in db_sku:
            one = {
                'userid'   : x['userid'],
                'uname'    : x['uname'],
                'nickname' : x.get('nickname',''),
                'licence'  : app_helper.image_url(x.get('upload_licence','')) if x.get('upload_licence','')!='' else '',
                'shop_pic' : [app_helper.image_url(x2) for x2 in x.get('shop_pic',[])] if x.get('shop_pic',[])!=[] else [],
                'status'   : x.get('user_role_status','WAIT'),
            }
            sku_data.append(one)

        num = db_sku.count()
        if num%PAGE_SIZE>0:
            num = num / PAGE_SIZE + 1
        else:
            num = num / PAGE_SIZE
        
        return render.check_employer(helper.get_session_uname(), helper.get_privilege_name(), sku_data,
            range(0, num))
