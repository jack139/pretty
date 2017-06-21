#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from config import setting
import helper

db = setting.db_web

# 课程和专辑的一些通用操作

# 修改专辑审核状态，同时修改所属课程的状态
def topic_change_status(tpc_id, status, comment='审核状态修改', check_comment=''):
    # 修改专辑状态
    update_set = {'status':status }
    if len(check_comment)>0:
        update_set['check_comment'] = check_comment

    db.topic_store.update_one({'tpc_id':tpc_id}, {
        '$set'  : update_set,
        '$push' : {
            'history' : (helper.time_str(), helper.get_session_uname(), comment), 
        }  # 纪录操作历史
    })

    # 专辑下商品同时更新状态
    db.obj_store.update_many({'obj_type':'topic', 'tpc_id':tpc_id}, {
        '$set':{'status':status},
    })

# 修改课程审核状态，
def obj_change_status(obj_id, status, comment='审核状态修改', check_comment=''):
    update_set = {'status':status }
    if len(check_comment)>0:
        update_set['check_comment'] = check_comment

    db.obj_store.update_one({'obj_id':obj_id}, {
        '$set'  : update_set,
        '$push' : {
            'history' : (helper.time_str(), helper.get_session_uname(), comment), 
        }  # 纪录操作历史
    })
