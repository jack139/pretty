#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/online/order_dispatch')

PRE_STATUS = {
    'DISPATCH' : 'PAID',
    'ONROAD'   : 'DISPATCH',
    'COMPLETE' : 'ONROAD'
}

STATUS_TIP = {
    'DISPATCH' : '开始拣货',
    'ONROAD'   : '开始配送',
    'COMPLETE' : '配送完成'
}

# 开始派送
class handler:
    def POST(self):
        web.header("Content-Type", "application/json")
        if helper.logged(helper.PRIV_USER,'BATCH_JOB'):
            param = web.input(order_id='', dest_status='') # dest_status in ['DISPATCH', 'ONROAD', 'COMPLETE']

            if '' in (param.order_id, param.dest_status):
                return json.dumps({'ret':-1, 'msg':'参数错误'})

            if not PRE_STATUS.has_key(param.dest_status):
                return json.dumps({'ret':-2, 'msg':'状态错误'})

            order_ids = param.order_id.split()
            print param.dest_status, order_ids

            changed = 0
            not_change = []

            for i in order_ids:
                condition = {
                    'status'  : PRE_STATUS[param.dest_status],
                    'order_id' : i,
                }

                # 更新订单状态，进入派送
                r = db.order_app.find_one_and_update(condition,
                    {
                        '$set' : {
                            'status'  : param.dest_status,
                            'man'     : 0,
                            param.dest_status : int(time.time()), # 2016-01-10, gt
                            'last_status': int(time.time()), 
                        },
                        '$push' : {'history' : (helper.time_str(), 
                            helper.get_session_uname(), STATUS_TIP[param.dest_status])} 
                    },
                    {'_id':1, 'uname':1}
                )

                if r:
                    changed += 1
                else:
                    not_change.append(i)

            if len(order_ids)==changed:
                return json.dumps({'ret':0,'msg':'订单已'+STATUS_TIP[param.dest_status]})
            else:
                return json.dumps({'ret':3,'msg':'部分订单前置状态不对: %s'%(','.join(not_change))})
        else:
            return json.dumps({'ret':-1,'msg':'无访问权限'})

