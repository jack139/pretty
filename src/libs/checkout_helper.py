#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import app_helper

db = app_helper.db

# 检查商品是否可售、调整价格等

def checkout_obj(uname, obj_id):
    # 检查用户是否已有此商品
    r2 = db.user_property.find_one({'userid':uname['userid'], 'obj_id':obj_id})
    if r2 and r2['status']=='paid': # 已购
        return {'ret' : -6, 'msg' : '已购此课程／专辑'}

    # 区别课程和专辑
    if obj_id[0]=='1': # 1 开头是课程，2 开头是专辑
        obj_type = 'course'
        r3 = db.obj_store.find_one({'obj_id' : obj_id})
    else:
        obj_type = 'topic'
        r3 = db.topic_store.find_one({'tpc_id' : obj_id})

    if r3 is None:
        return {'ret' : -5, 'msg' : '错误的object_id'}

    ret_data = {
        "ret"       : 0,
        "object_id" : obj_id,     # 唯一代码 
        "obj_type"  : obj_type,  # 类型
        "title"     : r3['title'],
        "due"       : r3.get('price',1),  # 应付金额，单位 分 , 默认1分
    }

    return ret_data