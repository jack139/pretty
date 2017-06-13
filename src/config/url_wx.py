#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

urls = [
    '/wx/',         'First',

    '/wx/init_pretty',    'InitPretty',
    '/wx/pretty_init',    'Pretty',

    '/wx/signature',    'WxSignature',
    '/wx/get_session',   'GetSessionId',
]

## ---- 分布式部署---------------------------------
app_dir = ['weixin']
app_list = []
for i in app_dir:
    tmp_list = ['%s.%s' % (i,x[:-4])  for x in os.listdir(i) if x[:2]!='__' and x.endswith('.pyc')]
    app_list.extend(tmp_list)
#print app_list

for i in app_list:
    # __import__('pos.audit', None, None, ['*'])
    tmp_app = __import__(i, None, None, ['*'])
    if not hasattr(tmp_app, 'url'):
        print tmp_app
        continue
    urls.extend((tmp_app.url, i+'.handler'))

# 最后一个
#urls.extend(('/([0-9|a-z]{24})', 'weixin.wxurl.handler')) #/([0-9|a-z]{24})   /(.+)

#print urls
#-----------------------------------------------------
