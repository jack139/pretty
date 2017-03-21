#!/usr/bin/env python
# -*- coding: utf-8 -*-

import app_helper

db=app_helper.db

BLACK_LIST = [ # 收货电话黑名单
    '15658744934',
    '17717625879',
    '13818759622',
    '17717625849',
    '13819958642',
    '17717169532',
    '13818876528',
    '13817886531',
    '13718990623',
    '13760627366',
    '13701807612',
    '13651968403',
    '13774346106',
    '18801790007',
]

# 检查黄牛

# 用收货电话检查黄牛, 可指定品号 
def check_mice(uname, rev_phone, product_id=None):  
    # 排除刷单号码
    if rev_phone=='12345678900':
        return False

    # 排除白名单
    if rev_phone in app_helper.WHITE_LIST:
        return False

    # 检查黑名单
    if rev_phone in BLACK_LIST:
        return True

    # 排除 非相关品号
    if product_id and product_id not in app_helper.CATCH_MICE:
        return False

    # 检查收货电话
    db_recv = db.recv_tel.find_one({'tel':rev_phone, 'product_id':product_id})
    if db_recv:
        one_more = 0
        if uname not in db_recv['unames']: # 补充疑似账号
            db.recv_tel.update_one({'tel':rev_phone, 'product_id':product_id},{'$push':{'unames':uname}})
            one_more = 1
        if len(db_recv['unames'])+one_more>3: # 限定限制数量
            # 发现 mice
            mice = 1
            for b in db_recv['unames']: 
                if b in app_helper.WHITE_LIST: # 过滤白名单相关号码
                    mice = 0
                    break
            # 保留代码，暂不拉黑
            #db.app_user .update_many({'uname':{'$in':db_recv['unames']}},{'$set':{'mice':mice}})
            #db.app_user .update_many({'openid':{'$in':db_recv['unames']}},{'$set':{'mice':mice}})
            #if one_more==1:
            #    db.app_user .update_one({'openid':uname},{'$set':{'mice':mice}})
            #    db.app_user .update_one({'uname':uname},{'$set':{'mice':mice}})
            if mice==1:
                print '!!! mice:', rev_phone
                return True
    else:
        db.recv_tel.insert_one({'tel':rev_phone, 'product_id':product_id, 'unames':[uname]})

    return False
