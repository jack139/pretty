#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper

db = setting.db_web

# 精品课程列表
url = ('/app/v1/list_course')

class handler: 
    @app_helper.check_sign(['app_id','dev_id','ver_code','tick','session',
            'category','page_size','page_index','sort_by'])
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        param = web.input(app_id='', dev_id='', ver_code='', session='', category='', 
            page_size='', page_index='', sort_by='1', tick='')

        if '' in (param.app_id, param.dev_id, param.ver_code, param.page_size, param.page_index, param.tick):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        if param.session!='':
            # 检查session登录
            uname = app_helper.app_logged(param.session) 
            if uname is None:
                return json.dumps({'ret' : -4, 'msg' : '无效的session'})
        else:
            uname = None

        #--------------------------------------------------
        cate_id = param['category'].strip() if param['category'].strip()!='' else app_helper.DEFAULT_CATEGORY

        r2 = db.online_cate_obj.find({
            'cate_id'   : cate_id, 
            'available' : 1,
        }, sort=[('sort_weight', 1)])

        obj_list = [i['obj_id'] for i in r2]

        if param.sort_by=='2': # 按销量排序
            r3 = db.obj_store.find({'obj_id' : {'$in' : obj_list}})            

            obj_data = {}
            for i in r3:
                obj_data[i['obj_id']]=i

            print obj_list
            obj_list = sorted(obj_list, key=lambda x:obj_data[x].get('volume',0), reverse=True)
            print obj_list

            # 取指定区间的
            start_pos = int(param.page_size)*int(param.page_index)
            end_pos = start_pos + int(param.page_size)
            obj_list_page = obj_list[start_pos:end_pos]

        else: # 按sort weight排序，性能比按销量高
            # 取指定区间的
            start_pos = int(param.page_size)*int(param.page_index)
            end_pos = start_pos + int(param.page_size)
            obj_list_page = obj_list[start_pos:end_pos]

            r3 = db.obj_store.find({'obj_id' : {'$in' : obj_list_page}})

            obj_data = {}
            for i in r3:
                obj_data[i['obj_id']]=i

        # 准备返回数据
        ret_obj_list = []
        for i in obj_list_page:
            if obj_data[i].get('status')!='PASSED': # 审核未通过，应该是上架后又有修改
                continue
            if len(obj_data[i]['image'])>0: # 取第1张图
                image_url = app_helper.image_url(obj_data[i]['image'][0])
            else:
                image_url = ''
            ret_obj_list.append({
                'object_id' : obj_data[i]['obj_id'], 
                'title'     : obj_data[i]['title'],
                'title2'    : obj_data[i]['title2'],
                'speaker'   : obj_data[i]['speaker'],
                'type'      : 1 if obj_data[i]['media']=='video' else 2,  # 1- 视频   2 － 音频  
                'image'     : image_url, 
                'length'    : obj_data[i]['length'],  # 长度，单位：秒
                'price'     : obj_data[i]['price'],  # 价格 单位：分
                'volume'    : obj_data[i]['volume'],  # 销量
            })

        ret_data = {
            "course" : ret_obj_list,
            "total" : len(ret_obj_list), # 返回的课程数量，小于 page_size说明到末尾 
            "page_size" : param.page_size, # 分页尺寸，与调用参数相同 
            "page_index" : param.page_index,  # 页索引 
        }

        # 返回
        return json.dumps({
            'ret'  : 0,
            'data' : ret_data,
        })
