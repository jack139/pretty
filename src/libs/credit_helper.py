#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import app_helper

db = app_helper.db


# 处理 余额 账户,  抽象 余额 操作

# 生成交易单
def make_trade_order(userid, amount, trade_type, comment, pay_type='cash'):
    trade_order = {
        'order_trade_id' : app_helper.get_new_order_id(),
        'userid'     : userid,
        'total_sum'  : amount,
        'trade_type' : trade_type, #  receipt 收款   refund 退款  consume 消费
        'pay_type'   : pay_type,
        'pay_time'   : app_helper.time_str(),
        'cash_sum'   : amount,
        'comment'    : comment,
    }
    db.order_trade.update_one({'order_trade_id':trade_order['order_trade_id']},
        {'$set':trade_order}, upsert=True)

    return trade_order['order_trade_id']


# 输入参数 ： 用户id: 用户唯一id

# 查询账户：余额／返利／合计总额
def check_balance(userid):
    credit_amount = 0

    r = db.cash_info.find_one({'userid':userid})
    if r:
        credit_amount = r['balance']

    return credit_amount


# 消费：，返回消费明细
def consume_balance(userid, cash_to_consume, comment='余额消费'):
    balance = check_balance(userid)

    if balance-cash_to_consume<0: 
        return False # 余额不足

    r = db.cash_info.find_one_and_update(
        {'userid':userid, 'balance':{'$gte':cash_to_consume}}, 
        {'$inc':{ 'balance' : -cash_to_consume}}
    )

    if r is None:
        return False # 余额不足

    # 生成交易单
    order_trade_id = make_trade_order(userid, cash_to_consume, 'consume', comment)

    return order_trade_id


# 退款：需提供退款明细，默认只返回到余额账户
def refund_balance(userid, cash_to_refund, trade_type='refund', comment='余额退款'):
    db.cash_info.update_one(
        {'userid':userid}, 
        {'$inc':{ 'balance' : cash_to_refund}},
        upsert=True
    )

    # 生成交易单
    order_trade_id = make_trade_order(userid, cash_to_refund, trade_type, comment)

    return order_trade_id


# 余额充值：余额账户, 只充值到参数给定的用户
def save_to_balance(userid, amount):
    return refund_balance(userid, amount, trade_type='receipt', comment='余额充值')



