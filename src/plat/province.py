#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time
from bson.objectid import ObjectId
from config import setting
import helper

db = setting.db_web

url = ('/plat/province')

class handler:
    def GET(self):
        if helper.logged(helper.PRIV_USER,'CITY_CODE'):
            render = helper.create_render()
            user_data=web.input(qtype='province', parent='1')

            r = []

            if user_data['qtype']=='province':
                r2 = db.code_province.find(sort=[('_id',1)])

                for i in r2:
                    r.append((
                        i['id'],
                        i['province_cname'],
                        '',
                        int(i.get('status',0)),
                    ))
                next = 'city'
                title = 'province'
                back = None
                back_id = '1'
            elif user_data['qtype']=='city':
                r3 = db.code_province.find_one({'id':user_data['parent']})

                r2 = db.code_city.find({'province_id':user_data['parent']}, sort=[('_id',1)])
                for i in r2:
                    r.append((
                        i['id'],
                        i['city_cname'],
                        r3.get('province_cname',''),
                        int(i.get('status',0)),
                    ))
                next = 'county'
                title = 'city'
                back = 'province'
                back_id = '1'
            elif user_data['qtype']=='county':
                r3 = db.code_city.find_one({'id':user_data['parent']})

                r2 = db.code_county.find({'city_id':user_data['parent']}, sort=[('_id',1)])
                for i in r2:
                    r.append((
                        i['id'],
                        i['county_cname'],
                        r3.get('city_cname',''),
                        int(i.get('status',0)),
                        #0 if i.get('limit_24') in [None, '', '0'] else int(i['limit_24']),
                        #0 if i.get('limit_freeze') in [None, '', '0'] else int(i['limit_freeze'])
                    ))
                next = None
                title = 'county'
                back = 'city'
                back_id = r3['province_id']
            else:
                return render.info('错误的参数！')

            return render.province(helper.get_session_uname(), helper.get_privilege_name(), 
                r, next, title, back, back_id, user_data['parent']
            )
        else:
            raise web.seeother('/')

    def POST(self):
        if helper.logged(helper.PRIV_USER,'CITY_CODE'):
            render = helper.create_render()
            user_data=web.input()

            if not user_data.has_key('qtype'):
                return render.info('错误的参数！')

            if user_data['qtype']=='province': # 保存省的设置
                for x in user_data.keys():
                    if not x.startswith('status'):
                        continue

                    qid = x.split('_')[1]

                    r1 = db.code_province.find_one({'id':qid})
                    if r1.get('status',0)!=int(user_data[x]): # 不同才修改
                        db.code_province.update_one({'id':qid},{
                            '$set'  : {'status':int(user_data[x])},
                            '$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '修改status')},
                        })

            elif user_data['qtype']=='city': # 保存市的设置
                for x in user_data.keys():
                    if not x.startswith('status'):
                        continue

                    qid = x.split('_')[1]

                    r1 = db.code_city.find_one({'id':qid})
                    if r1.get('status',0)!=int(user_data[x]): # 不同才修改
                        db.code_city.update_one({'id':qid},{
                            '$set'  : {'status':int(user_data[x])},
                            '$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '修改status')},
                        })

            elif user_data['qtype']=='county': # 保存县的设置
                for x in user_data.keys():
                    if x.startswith('status'):
                        qid = x.split('_')[1]

                        r1 = db.code_county.find_one({'id':qid})
                        if r1.get('status',0)!=int(user_data[x]): # 不同才修改
                            db.code_county.update_one({'id':qid},{
                                '$set'  : {'status':int(user_data[x])},
                                '$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '修改status')},
                            })
                        
                    elif x.startswith('limit_24'):
                        qid = x.split('_')[2]

                        r1 = db.code_county.find_one({'id':qid})
                        if r1.get('limit_24',0)!=int(user_data[x]): # 不同才修改
                            db.code_county.update_one({'id':qid},{
                                '$set'  : {'limit_24':int(user_data[x])},
                                '$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '修改limit_24')},
                            })

                    elif x.startswith('freeze'):
                        qid = x.split('_')[1]

                        r1 = db.code_county.find_one({'id':qid})
                        if r1.get('limit_freeze',0)!=int(user_data[x]): # 不同才修改
                            db.code_county.update_one({'id':qid},{
                                '$set':{'limit_freeze':int(user_data[x])},
                                '$push' : {'history' : (helper.time_str(), helper.get_session_uname(), '修改limit_freeze')},
                            })

            return render.info('保存成功！', '/plat/province?qtype=%s&parent=%s'%(user_data['qtype'],user_data.get('parent','1')))
        else:
            raise web.seeother('/')
