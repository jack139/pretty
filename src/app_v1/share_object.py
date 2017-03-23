#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 分享页面链接
url = ('/app/v1/share_object')

# 退出
class handler: 
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', object_id='', sign='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.object_id, param.session, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.dev_id, param.ver_code, param.session, param.object_id])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})

        # 检查session登录
        uname = app_helper.app_logged(param.session) 
        if uname is None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        #--------------------------------------------------

        ret_data = {
            "object_id" : param.object_id,     # 唯一代码 
            "type"  : 1,  # 类型： 1 课程, 2 专辑 
            "share_title" : "分享标题",
            "share_content" : "分享内容",
            "share_img" : "https://pretty.f8cam.com/static/image/banner/share.png",  # 分享图片 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
