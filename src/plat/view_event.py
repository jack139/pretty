#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web, time
from config import setting
import helper
#from libs import city_code

db = setting.db_web

url = ('/view_event')


# 查看订单
class handler:
    def GET(self):
        if helper.logged(helper.PRIV_USER):
            render = helper.create_render()
            user_data=web.input(todo='')
            
            if user_data.todo=='':
                return render.info('参数错误！')

            auth_level = -1
            session_uname = helper.get_session_uname()
            if session_uname in setting.auth_user:
                auth_level = 999
            elif session_uname in setting.cs_admin:
                auth_level = 1

            db_todo=db.order_app.find_one({'order_id': user_data.todo})
            if db_todo!=None:

                # 获取订单购物车中商品信息
                product_detail = []  # 产品及对应详情
                for index,u in enumerate(db_todo['cart']):
                    data = {
                        'product_id': u['product_id'],
                        'title': u['title'],
                        'num': int(u['num2']),
                        'price': '%.2f' % (float(u['price'])/int(u['num2'])),
                        'total_fee': u['price'],
                    }
                    product_detail.append(data)

                # due减去运费 2016-06-20 lf
                due_no_delivery = float(db_todo['due']) - float(db_todo.get('delivery_fee', '0.00'))
                # 计算总已退款金额
                old_refund_total = '0.00'
                if db_todo.get('refund_his', '') != '':
                    for fee in db_todo['refund_his']:
                        old_refund_total = float(old_refund_total)+float(fee.values()[0])
                max_refund_fee = '%.2f'%(float(db_todo['due']) - float(old_refund_total))

                # 地址省份
                county_name,_,_ = city_code.county_id_to_city_name(db_todo['address'][8])

                return render.view_event(helper.get_session_uname(), helper.get_privilege_name(), 
                    user_data.todo, db_todo, int(time.time()-db_todo['e_time']), 
                    auth_level, 
                    helper.ORDER_STATUS[db_todo['status']],
                    helper.REFUND_REASON, 
                    product_detail, 
                    due_no_delivery,
                    max_refund_fee,
                    county_name) # 授权客服才能修改
            else:
                return render.info('出错，请重新提交。')
        else:
            raise web.seeother('/')

    def POST(self):
        if helper.logged(helper.PRIV_USER):
            render = helper.create_render()
            user_data=web.input(todo='', status='', crmtext0='', crmtext='',reason= '',refund_fee=[])

            if '' in (user_data.status, user_data.todo):
                return render.info('错误的参数！')

            # 备注中的时间不能使用[]，避免和备注的时间点冲突
            if '[%s' % time.strftime('%Y-%m-%d',time.localtime(time.time())) in user_data['crmtext']:
                return render.info("备注中的日期不能用[]括起来！")

            db_todo=db.order_app.find_one({'order_id': user_data.todo})


            # 保存客服备注
            auth_level = -1
            session_uname = helper.get_session_uname()
            if session_uname in setting.auth_user:
                auth_level = 999
            elif session_uname in setting.cs_admin:
                auth_level = 1

            if user_data.status=='__CRM__':
                if user_data.crmtext0[0:3]=='n/a':
                    crmt = u'%s %s\r\n%s' % ('['+helper.time_str()+']', session_uname, user_data.crmtext.replace('\r\n', ';'))
                else:
                    crmt = u'%s%s %s\r\n%s' % (user_data.crmtext0, '['+helper.time_str()+']', session_uname, user_data.crmtext.replace('\r\n', ';'))
                db.order_app.update_one({'order_id':user_data.todo}, {'$set' : {'crm_text' : crmt, 'crm_time': helper.time_str()}})
                return render.info('保存完成', goto="/view_event?todo=%s" % user_data.todo)

            # 授权客服才能修改
            auth = False
            if session_uname in setting.cs_admin:
                auth = True 
            elif session_uname in setting.auth_user:
                auth = True

            if not auth:
                return render.info('无操作权限！')

            todo_update={
                'lock'      : 0,
                'e_time'      : int(time.time())
            }               
            comment = user_data.status # history 注释  

            if user_data.status not in  ['__NOP__', '__CHANGE_ADDR__']:
                todo_update['status']=user_data.status
                todo_update[user_data.status]=int(time.time()) # 记录状态时间


            if user_data.status=='__CHANGE_ADDR__':
                if db_todo['status'] in ['PAID', 'DISPATCH']: 
                    new_address = [
                        'modifed',
                        user_data.addr_name,
                        user_data.addr_tel,
                        user_data.addr_addr,
                        int(time.time()),
                        {
                            'lat': 0,
                            'lng': 0 },
                        '',
                        '',
                        db_todo['address'][8]
                    ]
                    todo_update['address'] = new_address
                    comment = '客服修改收货信息'
                else:
                    comment = '修改收货信息失败，订单状态不对'

            return_msg = '提交完成'

            if user_data.status=='CANCEL_TO_REFUND':
                if user_data.reason == '':
                    return render.info('请选择退款原因！','/view_event?todo=%s' % user_data.todo)
                if db_todo['status'] in ['CANCEL_TO_REFUND', 'FAIL_TO_REFUND'] and db_todo.get('refund_mark', '') == '':
                    return render.info('订单状态已是待退款状态','/view_event?todo=%s' % user_data.todo)
                reasons = dict()
                for i in refund_helper.REFUND_REASON:
                    reasons[i[1]] = i[0]
                
                print reasons
                reasonCode = user_data.reason
                print reasonCode
                reason = reasons[reasonCode]
                if db_todo.get('refund_mark', '') == 2:
                    todo_update['refund_mark'] = 4
                todo_update['reason_type'] = user_data.reason
                #todo_update['man'] = 1
                todo_update['cancel_user'] = session_uname
                todo_update['sum_to_refund'] = '%.2f' % float(user_data.sum_to_refund)
                comment = '客服取消订单'

                        
            r = db.order_app.find_one_and_update({'order_id':user_data.todo}, {
                '$set'  : todo_update,
                '$push' : {'history' : (helper.time_str(), session_uname, comment)}
            })
            #print r

            if r:
                pass

            #return render.info(return_msg ,goto="javascript:window.opener=null;window.close();",text2='关闭窗口')
            return render.info(return_msg, goto="/view_event?todo=%s" % user_data.todo,text2='返回订单详情')
        else:
            raise web.seeother('/')
