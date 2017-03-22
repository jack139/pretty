#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

urls2 = []

## ---- 分布式部署---------------------------------

app_dir = ['app_v1']
app_list = []

print 'pwd:', os.getcwd()

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
    urls2.extend((tmp_app.url, i+'.handler'))

#-----------------------------------------------------
