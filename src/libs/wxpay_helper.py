#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib3, hashlib
from config import setting
import app_helper

urllib3.disable_warnings()

api_key='0378881f16430cf597cc1617be53db37'
notify_url='http://%s:12048/app/wxpay_notify' % setting.app_host

def get_prepay_id(wx_appid, mch_id, trade_type, client_ip, order_id, total_fee, openid=None):
    nonce_str = app_helper.my_rand(30)

    if trade_type=='APP':
        body = 'U掌柜app'
        para = [
            ('appid'            , wx_appid),
            ('body'             , body),
            ('mch_id'           , mch_id),
            ('nonce_str'        , nonce_str),
            ('notify_url'       , notify_url),
            ('out_trade_no'     , order_id),
            ('spbill_create_ip' , client_ip),
            ('total_fee'        , total_fee),
            ('trade_type'       , trade_type)
        ]
    else: # trade_type == 'JSAPI'
        body = 'U掌柜微信'
        para = [
            ('appid'            , wx_appid),
            ('body'             , body),
            ('mch_id'           , mch_id),
            ('nonce_str'        , nonce_str),
            ('notify_url'       , notify_url),
            ('openid'           , openid),
            ('out_trade_no'     , order_id),
            ('spbill_create_ip' , client_ip),
            ('total_fee'        , total_fee),
            ('trade_type'       , trade_type)
        ]

    print para

    stringA = '&'.join('%s=%s' % i for i in para)
    stringSignTemp = '%s&key=%s' % (stringA, api_key)
    sign = hashlib.md5(stringSignTemp).hexdigest().upper()

    if trade_type=='APP':
        para_xml = '<xml>' \
            '<appid>'+wx_appid+'</appid>' \
            '<mch_id>'+mch_id+'</mch_id>' \
            '<nonce_str>'+nonce_str+'</nonce_str>' \
            '<sign>'+sign+'</sign>' \
            '<body>'+body+'</body>' \
            '<out_trade_no>'+order_id+'</out_trade_no>' \
            '<total_fee>'+total_fee+'</total_fee>' \
            '<spbill_create_ip>'+client_ip+'</spbill_create_ip>' \
            '<notify_url>'+notify_url+'</notify_url>' \
            '<trade_type>'+trade_type+'</trade_type>' \
            '</xml>'
    else:
        para_xml = '<xml>' \
            '<appid>'+wx_appid+'</appid>' \
            '<mch_id>'+mch_id+'</mch_id>' \
            '<nonce_str>'+nonce_str+'</nonce_str>' \
            '<sign>'+sign+'</sign>' \
            '<body>'+body+'</body>' \
            '<out_trade_no>'+order_id+'</out_trade_no>' \
            '<total_fee>'+total_fee+'</total_fee>' \
            '<spbill_create_ip>'+client_ip+'</spbill_create_ip>' \
            '<notify_url>'+notify_url+'</notify_url>' \
            '<trade_type>'+trade_type+'</trade_type>' \
            '<openid>'+openid+'</openid>' \
            '</xml>'

    print para_xml

    pool = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
    url = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
    r = pool.urlopen('POST', url, body=para_xml)

    return r


