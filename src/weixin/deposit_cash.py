#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper
from libs import wxpay_helper

db = setting.db_web

# 余额充值
url = ('/wx/deposit_cash')

# app使用的微信支付设置
wx_appid='wxebf6ce7906d3648b'
wx_appsecret='2653f845640f06a797c395f5b69b686a'
mch_id='1472056402'
api_key='0378881f16430cf597cc1617be53db37'
notify_url_wx='http://%s:8888/app/wxpay_notify' % setting.notify_host

class handler: 
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(session_id='', pay_sum='', pay_type='')

        if param.session_id=='':
            return json.dumps({'ret' : -1, 'msg' : 'session_id参数错误'})

        uname = app_helper.wx_logged(param.session_id)
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session_id'})

        if '' in (param.pay_sum, param.pay_type):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if not param['pay_sum'].isdigit():
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if int(param.pay_type)==3:
            pay_type='wxpay'
        else:
            return json.dumps({'ret' : -5, 'msg' : '错误的pay_type'})

        #--------------------------------------------------

        #生产充值流水号
        deposit_order_id = app_helper.get_new_order_id('vx','d').encode('utf-8')
        print 'new deposit_order_id', deposit_order_id

        wx_total_fee = '%d'%int(param['pay_sum'])
        ali_total_fee = '%.2f'%float(int(wx_total_fee)/100.0)


        # 微信支付，获得prepay信息
        if pay_type=='wxpay':
            if web.ctx.has_key('environ'):
                client_ip = web.ctx.environ['REMOTE_ADDR']
            else:
                return json.dumps({'ret' : -7, 'msg' : '无法取得客户端ip地址'})

            r = wxpay_helper.get_prepay_id(wx_appid, mch_id, 
                    'JSAPI', client_ip, deposit_order_id, wx_total_fee,
                    uname['openid'].encode('utf-8'))
            if r.status==200:
                wx_prepay_data = r.data
            else:
                return json.dumps({'ret' : -6, 'data' : r.status}) # 获取prepay信息错误
        else:
            wx_prepay_data = ''

        print wx_prepay_data

        # 生成充值订单
        new_deposit_order = {
            'userid'           : uname['userid'],
            'recharge_id'      : deposit_order_id,
            'order_trade_flow_id'   : '', # 交易记录的id，收到钱时候才填
            'create_time'      : app_helper.time_str(),
            'recharge_sum'     : wx_total_fee,  # 实际充值金额， 如果有满送，在这里处理
            'due'              : wx_total_fee,  # 实际应付的金额，支付成功时会核对这个金额
            'pay_type'         : pay_type, 
            'status'           : 'DUE',
            'wx_prepay_data'   : wx_prepay_data,
        }

        db.order_recharge.update_one(
            {'recharge_id' : deposit_order_id},
            {'$set' : new_deposit_order},
            upsert=True
        )

        ret_data = {
            'order_trade_id' : deposit_order_id,  # 实际返回的是充值订单号
            'pay_type'       : int(param.pay_type), 
            'notify_url'     : '', # 支付宝和微信的异步通知回调url
        }

        # 回调地址
        ret_data['notify_url'] = notify_url_wx
        print notify_url_wx

        if wx_prepay_data!='':
            try:
                import xml.etree.cElementTree as ET
            except ImportError:
                import xml.etree.ElementTree as ET

            xml=ET.fromstring(wx_prepay_data)
            ret_data['appid']  = xml.find('appid').text if xml.find('appid') is not None else ''
            ret_data['mch_id']  = xml.find('mch_id').text if xml.find('mch_id') is not None else ''
            ret_data['prepay_id']  = xml.find('prepay_id').text if xml.find('prepay_id') is not None else ''


        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
