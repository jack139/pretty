#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper
from libs import checkout_helper, credit_helper

db = setting.db_web

# 支付
url = ('/app/v1/pay_object')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session','object_id', 'pay_type'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', pay_type='', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, 
            param.pay_type, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------
        print uname

        # 检查是否可售
        r = checkout_helper.checkout_obj(uname, param.object_id)
        if r['ret']<0:
            return json.dumps({'ret' : r['ret'], 'msg' : r['msg']})            

        # 消费余额
        r2 = credit_helper.consume_balance(uname['userid'], r['due'], u'购买：'+r['title'])
        if r2==False:
            return json.dumps({'ret' : -9, 'msg' : '余额不足'})

        # 保存商品到用户资产
        db.user_property.update_one({'userid':uname['userid'], 'obj_id':param.object_id}, {'$set':{
            'obj_type'       : r['obj_type'],
            'status'         : 'paid',
            'order_trade_id' : r2
        }}, upsert=True)

        ret_data = {
            "pay_type"    : 0, # 支付类型 
            "order_trade_id" : r2, 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
