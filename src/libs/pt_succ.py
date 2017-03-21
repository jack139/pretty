#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
import time, random
import traceback, json
from bson.objectid import ObjectId
import app_helper,helper
from weixin.wx_lib import wx_event_push
from libs import coupon_helper
from libs import log4u
#from libs import sync_sku
from libs import sku_helper
from config import setting

db = setting.db_primary

# 填充成团

def get_num_to_diff(pt_order_id, get_wh_id=False):
    from libs import inventory_helper
    num_to_diff = 0
    order_app_docs = db.order_app.find({
        'pt_order_id' : pt_order_id,
        'status' : {'$nin' : ['DUE','CANCEL','TIMEOUT']}
    },{'cart':1, 'order_id':1, 'address':1, 'order_filter':1, 'region_id':1})

    warehouse_id = None

    print 'order_app_docs:', order_app_docs.count()

    print pt_order_id, order_app_docs.count()
    
    try:
        for x in order_app_docs:
            print 'order_id', x['order_id']

            if get_wh_id and x.has_key('order_filter') and warehouse_id==None:
                warehouse_id = inventory_helper.get_wh_shop_id(x['order_filter'], x['cart'][0].get('tuan_id'), x['region_id'])

            if x['address'][2] == '12345678900':
                print '内部刷单，不减库存', x['order_id']
                continue
            num_to_diff += x['cart'][0].get('num2',1)

    except KeyError:
        print 'KeyError'
        traceback.print_exc()
    
    if get_wh_id:
        return num_to_diff, warehouse_id
    else:
        return num_to_diff


# 最后一人参团，成团
def last_member_to_succ(pt_order_id, product_id, who):

    db.pt_order.update_one(
        { 'pt_order_id' : pt_order_id},
        { 
            '$set' : { 
                'status' : 'SUCC', 
                'succ_time' : app_helper.time_str(),
                'succ_tick' : int(time.time()),
                'last_status' : int(time.time()), # BI 统计用
            },
            '$push' : {'history':(app_helper.time_str(), who, '拼团成功')}
        }
    )
    
    # 所有团中PAID_AND_WAIT订单成为 PAID，准备拣货
    #r7 = db.order_app.find({ 'pt_order_id' : pt_order_id, 'status':'PAID_AND_WAIT' }, {'order_id':1})
    # 推MQ
    #for yy in r7:
    #    app_helper.event_push_mq(yy['order_id'],'PT_SUCC')

    db.order_app.update_many(
        { 'pt_order_id' : pt_order_id, 'status':'PAID_AND_WAIT' },
        {
            '$set'  : {
                'status'      :'PAID',
                'PAID'        : int(time.time()), # 2016-01-10, gt
                'last_status' : int(time.time()), # BI 统计用
            },
            '$push' : {'history':(app_helper.time_str(), who, '拼团成功')}
        }
    )

    r3=db.pt_order.find_one({ 'pt_order_id' : pt_order_id},
        {'member':1,'region_id':1,'succ_time':1,'pt_order_id':1, 'tuan_id':1,'type':1})

    # 推送订单
    for x in r3['member']:
        if x['order_id']!='this_is_a_blank_order':
            app_helper.event_push_order(x['order_id'])
            log4u.log('pt_succ', log4u.PT_SUCC , '拼团成功', x['order_id'])


    '''
    # 发消息
    print '发微信通知'

    try:
        wx_event_push.pt_success_notify(r3)
    except Exception, e:
        print 'Error', e
        traceback.print_exc()
        #pass

    #发"团长券"
    try:
        from weixin.coupon_logic.leader_coupon import handle_leader_coupon
        handle_leader_coupon(r3)
    except Exception, e:
        print "Error handle_leader_coupon ------------>", e
        traceback.print_exc()
        #pass
    '''

    # 发消息和发券让 backrun 去做， 2016-12-09，gt
    db.event_queue.insert_one({
        'type' : 'PT_SUCC_TAIL',
        'status' : 'WAIT',
        'data' : {
            'pt_order_id' : pt_order_id,
            'order_id' : pt_order_id[1:], # 团长的订单号
        }
    })


    # 减库存 2016-01-08, gt
    if product_id:
        #计算ptorder_id -> order_app['cart'][0]['num2']的和
        try:
            num_to_change, warehouse_id = get_num_to_diff(pt_order_id, get_wh_id=True)
        except Exception, e:
            print "get_num_to_diff: Error", e
            traceback.print_exc()
            num_to_change = 1

        print '拼团减库存：', num_to_change, product_id, warehouse_id

        if warehouse_id==None: # 防止 发货仓设置有问题
            #warehouse_id = setting.PT_shop[r3['region_id']]
            #print 'use default warehouse_id', warehouse_id
            print '不处理库存'
        else:
            r4 = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
                {
                    'product_id' : product_id,
                    #'shop'       : ObjectId(setting.PT_shop[r3['region_id']]),
                    'shop'       : ObjectId(warehouse_id), # 发货仓减库存 2016-07-05, gt
                },
                { 
                    '$inc'  : { 'num' : 0-num_to_change },
                    '$set'  : { 'last_update' : int(time.time())},
                },
                {'_id':1, 'num':1, 'shop':1, 'product_id':1}
            )
            #print num_to_change, r4
            if r4:
                print '库存检查', r4['num']-num_to_change, len(r3['member'])
                if r4['num']-num_to_change<len(r3['member']): # 库存小于成团人数就售罄
                    print '自动设置售罄'
                    # 相同品号商品设置“售罄”
                    #db.pt_store.update_many(
                    #    {
                    #        'product_id' : product_id,
                    #        'online' : r3['region_id'],  # 限定区域， 2016-05-19 gt
                    #    },{
                    #        '$set' :{'sale_out':1},
                    #        '$push':{'history':(app_helper.time_str(), 'system', '自动设置售罄')}
                    #    }
                    #)

                    # 此团设置“售罄”    # 2016-07-28 gt
                    db.pt_store.update_one(
                        {
                            'tuan_id' : r3['tuan_id'], 
                        },{
                            '$set' :{'sale_out':1},
                            '$push':{'history':(app_helper.time_str(), 'system', '自动设置售罄')}
                        }
                    )


def add_member_to_pt_order(pt_order_id, join_tick=None, is_leader=False):

    status = None
    comment = ''

    # 更新pt_order
    from libs import nickname
    rand_nickname = nickname.nickname[random.randint(0,len(nickname.nickname)-1)]
    rand_headimgurl = nickname.headimgurl[random.randint(0,len(nickname.headimgurl)-1)]

    r2 = db.pt_order.find_one_and_update(
        {
            'pt_order_id' : pt_order_id,
            'need'        : { '$gt' : 0 },
            'status'      : { '$in'  : ['OPEN', 'WAIT']}, # 已开团和等待开团状态
        }, 
        {
            '$push' : { 
                'member' : {
                    'openid'   : 'SYS_URFRESHER',
                    'position' : 'LEADER' if is_leader else 'MEMBER', 
                    'time'     : app_helper.time_str(join_tick),
                    'order_id' : 'this_is_a_blank_order',
                    'nickname' : rand_nickname,
                    'headimgurl' : rand_headimgurl,
                }
            },
            '$inc' : { 'need' : -1 }
        }
    )

    if r2==None:                            
        # pt_order 状态不是 OPEN 或 need==0, 取消本用户订单
        status = 'FAIL_TO_REFUND' # 参团失败，等待退款
        comment = ':参团失败-已成团'
    else:
        if r2['need']==1: #  最后一人, 成团！
            r8 = db.pt_store.find_one({'tuan_id':r2['tuan_id']},{'product_id':1})

            last_member_to_succ(pt_order_id, r8.get('product_id'), 'pt_succ')

            # 推 MQ， 当前订单导致成团
            for ont_member in r2['member']:
                if ont_member['order_id']!='this_is_a_blank_order':
                    print '自动成团，推PT_SUCC'
                    app_helper.event_push_mq(ont_member['order_id'],'PT_SUCC') 
                    break

            status = 'PAID'
            comment = ':成团'
        else:
            status = 'PAID_AND_WAIT'
            comment = ':已付款，待成团'

    print comment
    return status


# 填充快过期的OPEN活动
def add_tuan_to_succ_test(pt_order_id, num):
    
    #1、查找符合时限的pt_order
    this_tick = int(time.time())
    r2 = db.pt_order.find_one({'pt_order_id' : pt_order_id})

    #2、对符合条件的pt_order_doc#members自动填充
    x = r2

    if x['status']!='OPEN':
        print 'status', x['status']
        return None

    if x['need']==0: # 有出现可能
        print 'need==0'
        return None

    # 自动填充
    last_tick = int(time.mktime(time.strptime(x['member'][-1]['time'],"%Y-%m-%d %H:%M:%S")))
    for y in xrange(0,min(x['need'],num)): # 只散布在最近30分钟（1800秒）
        print 'auto_succ:', x['pt_order_id']
        add_member_to_pt_order(x['pt_order_id'], this_tick-random.randint(0,this_tick-last_tick))

    return True




# 支付成功时，处理拼团逻辑
def process_tuan_after_paid(r, who, creditpay=False):  # r 是订单数据，来自 order_app

    order_id = r['order_id']

    # 检查是否已在member中
    r1 = db.pt_order.find_one({
        'pt_order_id'   : r['pt_order_id'],
        'member.openid' : r['uname']
    })                

    if r1: # 已参团
        status = 'FAIL_TO_REFUND' # 参团失败，等待退款
        comment = ',参团失败-已参团'
        print '参团失败：已参团'

        if creditpay: # 余额支付时，检查是否存在同一订单重复支付的情况， 2017-01-10
            for xx in r1['member']:
                if xx['openid']==r['uname'] and xx['order_id']==order_id: # 余额重复支付，特殊处理
                    if r1['status']=='OPEN':
                        status = 'PAID_AND_WAIT' 
                    elif r1['status']=='SUCC':
                        status = 'PAID' 
                    comment = '..'
                    print 'Error: 余额重复支付，特殊处理', order_id
                    break
    else:
        # 更新销量
        db.pt_store.update_one({'tuan_id':r['cart'][0]['tuan_id']}, {'$inc':{'volume':1}})

        # 更新pt_order
        r2 = db.pt_order.find_one_and_update(
            {
                'pt_order_id' : r['pt_order_id'],
                'need'        : { '$gt' : 0 },
                'status'      : { '$in'  : ['OPEN', 'WAIT']}, # 已开团和等待开团状态
            }, 
            {
                '$push' : { 
                    'member' : {
                        'openid'   : r['uname'],
                        'position' : r['position'], 
                        'time'     : app_helper.time_str(),
                        'order_id' : order_id,
                    }
                },
                '$inc' : { 'need' : -1 }
            }
        )

        if r2==None:                            
            # pt_order 状态不是 OPEN 或 need==0, 取消本用户订单
            status = 'FAIL_TO_REFUND' # 参团失败，等待退款
            comment = ',参团失败-已成团'
            print '参团失败：已成团'
        else:
            if r2['need']==1: #  最后一人, 成团！
                # 最后一人订单设置为 PAID_AND_WAIT， 方便统一操作
                db.order_app.update_one({'order_id':order_id},{'$set':{'status':'PAID_AND_WAIT'}})

                # 推 MQ， 当前订单支付成功
                #app_helper.event_push_mq(order_id,'PAID') ＃ 在 api_router里推，这里推会没有 pay_type信息

                # 处理最后1人成团的事情
                last_member_to_succ(r['pt_order_id'], r['cart'][0].get('product_id'), who)

                status = 'PAID'
                comment = ',已成团'
            else:
                if r2['member']==[]: # 团长开团 
                    db.pt_order.update_one(
                        { 'pt_order_id' : r['pt_order_id']},
                        { 
                            '$set' : { 
                                'status' : 'OPEN', 
                                #'succ_time' : app_helper.time_str(),
                                #'succ_tick' : int(time.time()),
                                'last_status' : int(time.time()), # BI 统计用
                            },
                            '$push' : {'history':(app_helper.time_str(), who, '开团成功')}
                        }
                    )

                # 发支付成功后图文消息
                print '推图文消息'
                try:
                    wx_event_push.after_pay_notify(r['region_id'], r['uname'], r['cart'][0].get('tuan_id'), r)
                except Exception, e:
                    print 'Error', e
                    traceback.print_exc()

                status = 'PAID_AND_WAIT' # 已付款，待成团
                comment = ',待成团'

            try:
                wx_event_push.after_46h_notify(r['region_id'], r['uname'], r['cart'][0].get('tuan_id'), int(time.time()), r2)
            except Exception, e:
                print 'Error', e
                traceback.print_exc()
                
            # 使用的优惠券失效
            # 使用新抵用券 2016-02-29, gt
            if r['coupon']!=None:
                t_coupon = coupon_helper.coupon(uname=r['uname'],openid=r['uname'],unionid=r.get('unionid',''))
                if isinstance(r['coupon'], dict):
                    t_coupon.status_to_used(r['coupon']['coupon_id'], order_id)
                else: # 为兼容旧的coupon
                    t_coupon.status_to_used(r['coupon'][0], order_id) 

            # 添加分销订单记录 2016-04-08
            from libs import user_tree
            user_tree.add_order(r['uname'], order_id)

    return status, comment




# 支付成功时，处理1小时 逻辑
def process_1hour_after_paid(r, who, status):  # r 是订单数据，来自 order_app

    order_id = r['order_id']

    # 使用的优惠券失效 # app微信支付，和 公众号微信支付都从这返回
    # 使用新抵用券 2016-02-29, gt
    if r['coupon']!=None:
        t_coupon = coupon_helper.coupon(uname=r['uname'],openid=r['uname'],unionid=r.get('unionid',''))
        if isinstance(r['coupon'], dict):
            t_coupon.status_to_used(r['coupon']['coupon_id'], order_id)
        else: # 为兼容旧的coupon
            t_coupon.status_to_used(r['coupon'][0], order_id) 

    # 正常减库存！
    # item = [ product_id, num, num2, price]
    # k - num 库存数量
    print "修改库存."

    # 次日达订单 库存处理 2016-06-23， gt
    if r['type']=='NEXT_DAY':
        from libs import h24_helper
        ret_inventory = h24_helper.wms_update_inventory(order_id,r['shop'],r['cart'])
        if ret_inventory: # 标记已扣库存
            print '次日达订单扣wms库存成功'
            db.order_app.update_one({'order_id':order_id},{'$set':{'wms_update_inventory': 1}})
            # 推 MQ
            app_helper.event_push_mq(order_id,'ORDER_STOCK_REDUCE_SUCCESS') 
            log4u.log('pt_succ', log4u.REDUCE_STOCK , '次日达扣库存', order_id)

        print '==> 次日达 订单'
        # 先更新状态，否则push_order有可能失败“状态不是PAID”，2016-02-01， gt
        #db.order_app.update_one({'order_id':order_id},{'$set':{'status': status}})
        app_helper.event_push_order(order_id)

        return r['cart']

    # 1小时订单库存处理
    b2 = [] # C端商品
    for item in r['cart']:
        # 记录销售量
        #db.sku_store .update_one({'product_id' : item['product_id']},
        #    {'$inc' : {'volume' : float(item['num2'])}}
        #)
        sku_helper.inc_volume(item['product_id'], float(item['num2']))

        # 同步到运营中心
        #sync_sku.event_push_sku(item['product_id'])

        # 买X送Y
        try:
            # 活动数据从商品接口来 2017-01-09
            r9 = sku_helper.get_inventory_by_product_id(item['product_id'], r['shop']) 
            sale_promotes = r9['sale_promotes'] if r9 else None

            from libs import settings_helper
            sale_promote = settings_helper.is_buy_x_give_y(item['product_id'], sale_promotes)
        except Exception, e:
            print 'Error', e
            traceback.print_exc()
            sale_promote = None

        if sale_promote:
            if item.has_key('numyy'): # v3 2015-10-25
                print '买X送Y'


        # 过滤数量价格为零的
        if item['num2']==0 and float(item['price'])==0.0:
            continue

        # num2 实际购买数量, numyy 赠送数量， v3之后才有munyy  2015-10-20
        num_to_change = float(item['num2']) + float(item.get('numyy', 0.0))
        r2 = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
            {
                'product_id' : item['product_id'],
                'shop'       : r['shop'],
            },
            { 
                '$inc'  : { 
                    'num'         : 0-num_to_change, # num2 实际购买数量
                    'pre_pay_num' : num_to_change, # 记录预付数量
                },
                '$set'  : { 'last_update' : int(time.time())},
                #'$push' : { 'history' : (helper.time_str(), 
                #   helper.get_session_uname(), '售出 %s' % str(item['num']))},
            },
            {'_id':1}
        )
        #print r
        #if r2==None: # 不应该发生
        #    return json.dumps({'ret' : -9, 'msg' : '修改库存失败，请联系管理员！'})
        #else:
        #    b2.append(item)
        b2.append(item)


        # 更新第3方库存 2015-10-10
        try:
            helper.elm_modify_num(r['shop'], item['product_id'])
            print ">>>>pt_succ elm_modify_num success %s" % item['product_id']
        except Exception,e:
            print ">>>>pt_succ elm_modify_num fail,%s" % str(e)
            traceback.print_exc()


    # 手机号码登录下单，或微信登录绑定手机号再下单，则判断是否有推荐的老客，给老客发券2016-06-30 lf
    print ">>>pt_succ param unionid %s" % r.get('unionid','n/a')
    try:
        from weixin.wx_lib import wx_helper
        from libs import app_user_helper

        if len(r['uname']) != 11 and r.get('unionid', '') != '':
            #uname = db.unionid_index .find({'unionid': r['unionid']}, {'uname': 1})
            uname = app_user_helper.get_user_list_by_unionid(r['unionid'])
            # 微信登录支付但未绑定手机号则老客不发券
            for u in uname:
                if len(u.get('uname', '')) == 11:
                    wx_helper.give_coupon_to_old(u['uname'], order_id)
        else:
            wx_helper.give_coupon_to_old(r['uname'], order_id)
    except Exception, e:
        print "Error: >>>%s give_coupon_to_old fail %s" % (r['uname'], str(e))


    # 检查是否有b3商品, 3种情况
    # 1. b2, b3 都有，拆单
    # 2. 只有b3，站点改为B3站点，保留收货站点
    # 3. 只有b2，保持订单不变
    #print b2

    print "1小时订单保持不变"

    from libs import h01_helper
    #if str(r['shop']) in h01_helper.H01_SHOP.keys():
    ret_inventory = h01_helper.wms_update_inventory(order_id,r['shop'],r['cart'])
    if ret_inventory: # 标记已扣库存
        print '1小时订单扣wms库存成功'
        db.order_app.update_one({'order_id':order_id},{'$set':{'wms_update_inventory': 1}})
        # 推 MQ
        app_helper.event_push_mq(order_id,'ORDER_STOCK_REDUCE_SUCCESS') 
        log4u.log('pt_succ', log4u.REDUCE_STOCK , '1小时扣库存', order_id)


    # 推送1小时订单 2016-08-19 gt
    print '==> 次日达 订单'
    app_helper.event_push_order(order_id)

    return b2



# 支付成功时，处理商家商品 逻辑:
# 1, 商家订单支付成功后拆单, 子单类型 type='MALL_SON', 都放在order_app里，
#    order_id= 父单order_id+cart??(购物车name),  只有一个购物车时也会添加一个子单
# 2, 分配余额支付比例
# 3, 使用的优惠券失效 # 多家多张抵用券失效
# 4, 减库存，商家商品库存 inverntory MALL_shop 里

def make_son_order(parent_order):
    for cart in parent_order['cart_list']:
        order = {
            'status'          : 'PAID',
            'uname'           : parent_order['uname'],
            'shop'            : parent_order['shop'],
            'user'            : parent_order['user'],
            'order_id'        : parent_order['order_id']+cart['name'],
            'parent_order_id' : parent_order['order_id'],
            'order_source'    : parent_order['order_source'],
            'address'         : parent_order['address'], # 收货地址

            'coupon'          : cart['coupon'],  # 使用的优惠券
            'cart'            : cart['cart'],
            'cost'            : cart['cost'], # 成本合计，参考
            'total'           : cart['total'], # 价格小计，加项
            'coupon_disc'     : cart['coupon_disc'], # 优惠券抵扣，减项
            'first_disc'      : cart.get('first_disc','0.00'), # 首单立减， 减项
            'delivery_fee'    : cart['delivery_fee'], # 运费，加项
            'due'             : cart['due'], # 应付总金额 2015-11-24

            'openid'          : parent_order['openid'],
            'unionid'         : parent_order['unionid'], # 2016-03-01, gt
            'app_uname'       : parent_order['app_uname'],
            'uname_id'        : parent_order['uname_id'],
            'type'            : 'MALL_SON',

            'comment'         : '',
            'b_time'          : int(time.time()),
            'e_time'          : int(time.time()),
            'poly_shop'       : parent_order['poly_shop'], # 是否匹配到门店 2015-10-18

            'credit_total'    : '0.00', # 余额支付金额
            'use_credit'      : '0.00', # 部分支付时，余额支付金额
            'due3'            : '0.00', # 第3方应付金额   use_credit + due3 = due

            'history'         : parent_order['history'],
            'paid_time'       : parent_order['paid_time'],
            'paid_tick'       : parent_order['paid_tick'],
        }

        parent_use_credit_amount = float(parent_order.get('use_credit', '0'))
        if parent_use_credit_amount>0:
            use_credit_amount = parent_use_credit_amount*float(order['due'])/float(parent_order['due'])
            due3_amount = float(order['due']) - use_credit_amount
            order['credit_total'] = order['use_credit'] = '%.2f'%use_credit_amount
            order['due3'] = '%.2f'%due3_amount
        else:
            order['due3'] = order['due']

        db.order_app.insert_one(order) # 增加子订单


def process_mall_after_paid(rr, who):  # rr 是订单数据，来自 order_app

    order_id = rr['order_id']

    t_coupon = coupon_helper.coupon(uname=rr['uname'],openid=rr['uname'],unionid=rr.get('unionid',''))

    b2s = rr['cart_list']

    for r in b2s: # 处理多个购物车

        # 使用的优惠券失效 
        # 使用新抵用券 
        if r['coupon']!=None:
            if isinstance(r['coupon'], dict):
                t_coupon.status_to_used(r['coupon']['coupon_id'], order_id)
            else: # 为兼容旧的coupon
                t_coupon.status_to_used(r['coupon'][0], order_id) 

        # 正常减库存！
        # item = [ product_id, num, num2, price]
        # k - num 库存数量
        print "修改库存."

        b2 = [] # C端商品
        for item in r['cart']:
            # 记录销售量
            #db.sku_store .update_one({'product_id' : item['product_id']},
            #    {'$inc' : {'volume' : float(item['num2'])}}
            #)
            sku_helper.inc_volume(item['product_id'], float(item['num2']))

            # 同步到运营中心
            #sync_sku.event_push_sku(item['product_id'])

            # 买一送一
            #if item['product_id'] in app_helper.buy_X_give_Y.keys():
            #    print '买X送Y'

            # 过滤数量价格为零的
            if item['num2']==0 and float(item['price'])==0.0:
                continue

            # num2 实际购买数量, numyy 赠送数量， v3之后才有munyy  2015-10-20
            num_to_change = float(item['num2']) + float(item.get('numyy', 0.0))
            r2 = db.inventory.find_one_and_update(  # 不检查库存，有可能负库存
                {
                    'product_id' : item['product_id'],
                    'shop'       : ObjectId(setting.MALL_shop),
                },
                { 
                    '$inc'  : { 
                        'num'         : 0-num_to_change, # num2 实际购买数量
                        #'pre_pay_num' : num_to_change, # 记录预付数量
                    },
                    '$set'  : { 'last_update' : int(time.time())},
                    #'$push' : { 'history' : (helper.time_str(), 
                    #   helper.get_session_uname(), '售出 %s' % str(item['num']))},
                },
                {'_id':1}
            )
            #print r
            if r2==None: # 不应该发生
                return json.dumps({'ret' : -9, 'msg' : '修改库存失败，请联系管理员！'})
            else:
                b2.append(item)

        r['cart'] = b2

    make_son_order(rr) # 添加子单，

    return b2s

# 字段开新团, 开团成功返回 pt_order_id, 失败返回 None
def auto_new_tuan(region_id, tuan_id):
    # 取团信息
    db_pt_sku = db.pt_store.find_one({'tuan_id':tuan_id})
    if db_pt_sku==None:
        return None

    now_tick = int(time.time())

    if db_pt_sku['sale_out']==1:
        print '此拼团活动已售罄'
        return None

    if region_id not in db_pt_sku['online']:
        print '该拼团活动下架'
        return None

    if db_pt_sku['expire_tick']<now_tick:
        print '该拼团活动过期', db_pt_sku['expire_tick'], now_tick
        return None

    # 生成新 pt_order_id
    order_id = app_helper.get_new_order_id('v5', 't')
    pt_order_id = pt_order_id = 'pt' + order_id[1:] 

    # 准备开团数据
    expire_hour = 24 # 测试1小时
    new_pt_order = {
        'tuan_id'     : tuan_id,
        'pt_order_id' : pt_order_id, 
        'region_id'   : region_id,
        'expire_tick' : now_tick+3600*expire_hour,
        'expire_time' : app_helper.time_str(now_tick+3600*expire_hour),
        'create_tick' : now_tick,
        'create_time' : app_helper.time_str(),
        'leader'      : 'SYS_URFRESHER',
        'member'      : [],
        'need'        : db_pt_sku['tuan_size'],
        'tuan_size'   : db_pt_sku['tuan_size'], # 记录团大小，BI使用
        'type'        : 'TUAN',
        'status'      : 'OPEN', # 开团
    }

    db.pt_order.insert_one(new_pt_order)
    
    # 添加团长
    add_member_to_pt_order(pt_order_id, is_leader=True)

    return pt_order_id

