#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os
import time, json, hashlib
from config import setting
import app_helper

db = setting.db_web

url = ('/app/v1/list_banner')


# 获取轮播图（不需要session）
class handler: 
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', sign='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.dev_id, param.ver_code])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        #--------------------------------------------------


        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : {
                'banner' : {
                    [
                        {
                            'image' : 'https://pretty.f8cam.com/static/image/banner/1.png',
                            'click' : 'http://baidu.com',
                        },
                        {
                            'image' : 'https://pretty.f8cam.com/static/image/banner/2.png',
                            'click' : '',
                        },
                    ]
                }
            }
        })
