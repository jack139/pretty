#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, json, hashlib, time
from bson.objectid import ObjectId
from config import setting
import app_helper
import app_rules_v5 as app_rules
from order_checkout import checkout
from libs import credit_helper
from libs import log4u

db = setting.db_primary

url = ('/app/v1/creditpay')

# 余额下单
class handler:
    def POST(self):
        web.header('Content-Type', 'application/json')

        param = web.input(app_id='', session='', order_id='', total='', note='', delivery_time='', sign='')

        print param

        if '' in (param.app_id, param.session, param.total, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        uname = app_helper.app_logged(param.session) # 检查session登录
        if uname:
            #验证签名
            md5_str = app_helper.generate_sign([param.app_id, param.session, 
                param.order_id, param.total, param.note, param.delivery_time])
            if md5_str!=param.sign:
                return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

            #db_shop = db.base_shop.find_one({'_id':ObjectId(setting.default_shop)},{'name':1})

            if len(param.order_id)>0:
                print param.order_id

                db_order = db.order_app.find_one({'order_id':param.order_id})
                if db_order['status']!='DUE':
                    print '============================== -100'
                    return json.dumps({'ret' : -100, 'msg' : '订单状态变化，请确认'})

                # 团购检查
                if db_order.get('type') in ['TUAN', 'SINGLE']:
                	# 团购开通余额支付
                    ret_json = app_rules.checkout_pt_order_again(
                        uname, param.app_id, param.session, db_order
                    )
                    ret_json = json.loads(ret_json)
                elif db_order.get('type') == 'MALL':
                    '''
                    ret_json = mall_checkout(uname, {
                        'session'   : param.session,
                        'order_id'  : param.order_id,
                        'shop_id'   : setting.MALL_shop,
                        'addr_id'   : db_order['address'][0],
                        'coupon_id' : db_order['coupon'],
                        'cart'      : json.dumps(app_rules.covert_cart_list_to_cart(db_order['cart_list'])),
                        'app_id'    : param.app_id,
                        'use_credit': '1' if float(db_order.get('use_credit','0'))>0 else '', #2015-11-19
                    })
                    '''
                    pass
                else:
                    ret_json = checkout(db_order.get('version','v3'), uname, {  # 假扮 v3 调用
                        'session'   : param.session,
                        'order_id'  : param.order_id,
                        'shop_id'   : str(db_order['shop']),
                        'addr_id'   : db_order['address'][0],
                        'coupon_id' : db_order['coupon']['coupon_id'] if float(db_order['coupon_disc'])>0 else '',
                        'cart'      : json.dumps(db_order['cart']),
                        'app_id'    : param.app_id,
                        'use_credit': '1' if float(db_order.get('use_credit','0'))>0 else '', #2015-11-19
                        'delivery_id' : db_order.get('delivery_id', ''),
                    })
                if ret_json['ret']<0:
                    # checkout 出错
                    return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

                if ret_json['data'].has_key('alert') and ret_json['data']['alert']==True:
                    # checkout 返回message
                    return json.dumps({'ret' : -100, 'msg' : ret_json['data']['message']})

                #if float(ret_json['data']['use_credit'])!=float(db_order['use_credit']): # 不用判断due3，因为全额用余额支付
                #ret_due = float(ret_json['data']['use_credit'])
                #db_due = float(db_order['use_credit'])
                ret_due = float(ret_json['data']['due']) # 不能用 use_credit做判断，1.3版会有问题
                db_due = float(db_order.get('due3', db_order['due']))
                #db_due = float(db_order['due'])

                ret_credit = float(ret_json['data']['use_credit']) # 
                db_credit = float(db_order.get('use_credit', 0))

                #if abs(ret_due - db_due) >= 0.01:
                if abs(ret_credit - db_credit) >= 0.01: # 2016-08-13 gt
                    # checkout后金额有变化，说明库存或优惠券有变化
                    print 'checkout后金额有变化，说明库存或优惠券有变化'
                    db.order_app.update_one({'order_id':param.order_id},{
                        '$set'  : {
                            'status' : 'CANCEL',
                            'CANCEL' : int(time.time()), # 2016-01-10, gt
                            'last_status' : int(time.time()), 
                        },
                        '$push' : {'history':(app_helper.time_str(), uname['uname'], '订单取消(余额)')}
                    })
                    # 订单推MQ
                    app_helper.event_push_mq(param.order_id, 'CANCEL')

                    print '============================== -101'
                    print 'db_order', db_order
                    return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，订单已取消，请重新下单'})


                # 判断余额
                credit_balance = credit_helper.check_balance(uname['uname'])
                if round(float(db_order['due']),2)>round(credit_balance['total'],2):
                    print '============================== -102'
                    return json.dumps({'ret' : -100, 'msg' : '余额不足'})

                if abs(ret_due-float(param.total))>0.05:
                    # 防止total_fee 与 due 不一致，误差不能大于5分， 2016-02-03， gt
                    print '============================== -103'
                    return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单 .'})

                # 可支付
                db.order_app.update_one({'order_id':param.order_id},{
                    '$push' : {'history':(app_helper.time_str(), uname['uname'], '提交余额支付2')}
                })
                return json.dumps({'ret' : 0, 'order_id' : param.order_id})

            else:
                # 判断余额
                credit_balance = credit_helper.check_balance(uname['uname'])
                if round(float(param.total),2)>round(credit_balance['total'],2):
                    print '============================== -104'
                    return json.dumps({'ret' : -100, 'msg' : '余额不足'})

                db_cart = db.app_user.find_one({'uname':uname['uname']},{'cart_order.%s'%param.session:1})

                # 拼团订单
                if isinstance(db_cart['cart_order'][param.session], list):
                    # 生成order_id
                    order_id = app_helper.get_new_order_id('v5', 't')
                    return app_rules.pay_pt_order(db, param, db_cart['cart_order'][param.session],
                                                  order_id, param.note, uname, pay_type='credit')

                # 生成order_id
                new_order = dict(db_cart['cart_order'][param.session])
                order_prefix = 'm' if new_order['type']=='MALL' else 'n' # 区分 1小时订单和 商家订单
                order_id = app_helper.get_new_order_id('v5', order_prefix)

                print 'new order_id', order_id
                
                # 生成新订单
                new_order['order_id']=order_id
                new_order['deadline']=int(time.time())+60*15
                new_order['status']='DUE'
                new_order['user_note']=param.note.strip()
                new_order['delivery_time']=param.delivery_time
                new_order['history']=[(app_helper.time_str(), uname['uname'], '提交余额支付')]

                if new_order.get('type') == 'MALL':
                    '''
                    ret_json = mall_checkout(uname, {
                        'session'   : param.session,
                        'order_id'  : order_id,
                        'shop_id'   : setting.MALL_shop,
                        'addr_id'   : new_order['address'][0],
                        'coupon_id' : new_order['coupon'],
                        'cart'      : json.dumps(app_rules.covert_cart_list_to_cart(new_order['cart_list'])),
                        'app_id'    : param.app_id,
                        'use_credit': '1' if float(new_order.get('use_credit','0'))>0 else '', #2015-11-19
                    })
                    '''
                    pass
                else:
                    if not new_order['address']:
                        return json.dumps({'ret' : -100, 'msg' : '请选择收货地址'})

                    ret_json = checkout(new_order.get('version','v3'), uname, {  # 假扮 v3 调用
                        'session'   : param.session,
                        'order_id'  : order_id,
                        'shop_id'   : str(new_order['shop']),
                        'addr_id'   : new_order['address'][0],
                        'coupon_id' : new_order['coupon']['coupon_id'] if float(new_order['coupon_disc'])>0 else '',
                        'cart'      : json.dumps(new_order['cart']),
                        'app_id'    : param.app_id,
                        'use_credit': '1' if float(new_order.get('use_credit','0'))>0 else '', #2015-11-23
                        'delivery_id' : new_order.get('delivery_id', ''),
                    })

                if ret_json['ret']<0:
                    # checkout 出错
                    db.order_app.delete_one({'order_id':order_id}) # 2016-03-17，删除空订单
                    return json.dumps({'ret' : ret_json['ret'], 'msg' : ret_json['msg']})

                if ret_json['data'].has_key('alert') and ret_json['data']['alert']==True:
                    # checkout 返回message
                    db.order_app.delete_one({'order_id':order_id}) # 2016-03-17，删除空订单
                    return json.dumps({'ret' : -100, 'msg' : ret_json['data']['message']})

                #if float(ret_json['data']['use_credit'])!=float(new_order['use_credit']):
                ret_due = float(ret_json['data']['due']) # 不能用 use_credit做判断，1.3版会有问题
                db_due = float(new_order.get('due3', new_order['due']))
                #db_due = float(new_order['due'])
                #if abs(ret_due - db_due) >= 0.01:
                #    # checkout后金额有变化，说明库存或优惠券有变化
                #    print '============================== -105'
                #    #print 'new_order', new_order
                #    db.order_app.delete_one({'order_id':order_id}) # 2016-03-17，删除空订单
                #    return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单 ..'})

                ret_credit = float(ret_json['data']['use_credit']) # 
                db_credit = float(new_order.get('use_credit', 0))
                if abs(ret_credit - db_credit) >= 0.01:
                    # checkout后金额有变化，说明库存或优惠券有变化
                    print '============================== -105'
                    #print 'new_order', new_order
                    db.order_app.delete_one({'order_id':order_id}) # 2016-03-17，删除空订单
                    return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单 ..'})

                if abs(ret_due-float(param.total))>0.05:
                    # 防止total_fee 与 due 不一致，误差不能大于5分， 2016-02-03， gt
                    print '============================== -106'
                    db.order_app.delete_one({'order_id':order_id}) # 2016-03-17，删除空订单
                    return json.dumps({'ret' : -100, 'msg' : '很抱歉，数据异常，请重新下单 ...'})

                #db.order_app.insert_one(new_order)
                db.order_app.update_one({'order_id':order_id},{'$set':new_order}, upsert=True) # 2016-03-17,gt
                # 订单推MQ
                app_helper.event_push_mq(order_id, 'DUE')
                log4u.log('creditpay', log4u.DUE , '生成订单', order_id)

                return json.dumps({'ret' : 0, 'order_id' : order_id})
        else:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})
