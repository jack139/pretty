#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json
from config import setting
import app_helper
from libs import settings_helper
from libs import app_user_helper

db = setting.db_web

url = ('/app/v1/get_settings')


# 检查随机码
class handler: # CheckRand:
    def POST(self, version='v1'):
        web.header('Content-Type', 'application/json')
        #print web.input()
        param = web.input(app_id='', session='', rand='', invitation='', sign='')

        if '' in (param.app_id, param.session, param.rand, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        #验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.session, param.rand, param.invitation])
        if md5_str!=param.sign:
            return json.dumps({'ret' : -1, 'msg' : '签名验证错误'})
        return CheckRand.check_rand(param, version)

    @staticmethod
    def check_rand(param, version='v1'):
        session = app_helper.get_session(param.session)
        if session==None:
            return json.dumps({'ret' : -4, 'msg' : '无效的session'})

        if session.get('pwd_fail',0)>=5:
            print '========> 请重新获取验证码', session.get('pwd_fail',0)
            return json.dumps({'ret' : -5, 'msg' : '请重新获取验证码'})

        if param.rand.strip()!=session['rand']:
            #2015-12-22,gt
            if session['uname'] in app_helper.INNER_NUM.keys() and param.rand.strip()==app_helper.INNER_NUM[session['uname']]:
                pass
            #elif session['uname'] in setting.inner_number.keys() and \
            #    param.rand.strip()==setting.inner_number[session['uname']]:
            #    None
            else:
                db.app_sessions.update_one({'session_id':session['session_id']},{'$inc':{'pwd_fail':1}})
                return json.dumps({'ret' : -5, 'msg' : '短信验证码错误'})

        db.app_sessions.update_one({'session_id':session['session_id']},{'$set':{
            'login'  : 1,
            'attime' : time.time(),
        }})

        #邀请码
        #invitation = param.get('invitation', '').lower()
        #if invitation == '2016':
        #    #r = db.app_user .find_one({'uname' : session['uname']},{'invitation':1})
        #    r = app_user_helper.get_user_info(session['uname'], q_type='uname')
        #    if r.get('invitation', '')!='': # 已填邀请码
        #        invitation = ''
        #elif param.has_key('invitation'):

        #    if db.invitation.find({'code': invitation}).count()==0: # 无效地推邀请码
        #        #if db.app_user .find({'my_invit_code': invitation}).count()==0: # 无效用户邀请码
        #        if invitation!='' and app_user_helper.get_user_by_invit_code(invitation)==None: # 无效用户邀请码
        #            invitation = ''
        #    if invitation != '':
        #        #r = db.app_user .find_one({'uname' : session['uname']},{'invitation':1})
        #        r = app_user_helper.get_user_info(session['uname'], q_type='uname')
        #        if r.get('invitation', '')!='': # 已填邀请码
        #            invitation = ''
        #else:
        #    invitation = ''

        invitation = ''

        invitation_coupon = 0
        #print '>>>>>>>>> coupou_invitation:', invitation
        #if invitation == '2016':
        #    #r = db.app_user .find_one_and_update({'uname' : session['uname']},{
        #    #    '$set'  : {'invitation' : invitation, 'last_time' : app_helper.time_str()},
        #    #}, {'address':1, 'new_coupon':1})
        #    app_user_helper.update_user_info(session['uname'], 'uname', {'invitation' : invitation})
        #    r = db.app_user.find_one({'uname' : session['uname']}, {'new_coupon':1}#)

        #    # 新抵用卷格式 2016-02-28, gt
        #    invitation_coupon = settings_helper.give_coupon_to_user(
        #        coupon_active_code = app_helper.COUPON_SET['INVIT2016'],
        #        uname=session['uname'],
        #        unionid=session['unionid']
        #    #)

        #elif invitation!='':
        #    # 赠送优惠券
        #    #r = db.app_user .find_one_and_update({'uname' : session['uname']},{
        #    #    '$set'  : {'invitation' : invitation, 'last_time' : app_helper.time_str()},
        #    #}, {'address':1, 'new_coupon':1})
        #    app_user_helper.update_user_info(session['uname'], 'uname', {'invitation' : invitation})
        #    r = db.app_user.find_one({'uname' : session['uname']}, {'new_coupon':1}#)

        #    # 注册发抵用券 2016-01-14, gt
        #    # 新抵用卷格式 2016-02-28, gt
        #    invitation_coupon = settings_helper.give_coupon_to_user(
        #        coupon_active_code = app_helper.COUPON_SET['INVIT'],
        #        uname=session['uname'],
        #        unionid=session['unionid']
        #    #)

        #else:
        #    #r = db.app_user .find_one_and_update({'uname' : session['uname']},{
        #    #    '$set'  : {'last_time' : app_helper.time_str()}
        #    #}, {'address':1, 'new_coupon':1})
        #    r = db.app_user.find_one({'uname' : session['uname']}, {'new_coupon':1})

        # 更新登录时间 2016-12-28， gt
        app_user_helper.update_user_info(session['uname'], 'uname', {'last_time' : app_helper.time_str()})

        r = db.app_user.find_one({'uname' : session['uname']}, {'new_coupon':1})

        #if r is not None and len(r['address'])>0: # 应该实现：返回最近使用的地址 !!!!
        #    addr = {
        #        'id'   : r['address'][0][0],
        #        'name' : r['address'][0][1],
        #        'tel'  : r['address'][0][2],
        #        'addr' : r['address'][0][3],
        #    }
        #else:
        addr = {}

        # 返回
        if version=='v3':
            # 是否为新用户
            user_new = False
            # 是否有新收到的抵用券，进行提示
            if r is not None and r.has_key('new_coupon') and r['new_coupon']>0:
                alert = True
                #message = '掌柜送您%d张抵用券，请在个人中心查看哦' % (r['new_coupon']+invitation_coupon)
                message = '恭喜您获得新用户专享抵用券大礼包，可在个人中心查看哦'
                pop_message = '恭喜您，领取成功!'
                user_new = True
                db.app_user.update_one({'uname':session['uname']},{'$set':{'new_coupon':0}})
            else:
                alert = False
                message = ''
                pop_message = '现在下单还有很多优惠哦~'

            if session['unionid'] != '':
                if_bind = True
                wx_nickname = ''
                wx_img = ''
                openid = ''
                #uid_list = db.unionid_index .find({'unionid': session['unionid']})
                uid_list = app_user_helper.get_user_list_by_unionid(session['unionid'])
                for u in uid_list:
                    if u.get('openid'):
                        #user = db.app_user .find_one({'openid':u['openid']})
                        user = app_user_helper.get_user_info(u['openid'], q_type='openid')
                        if user:
                            openid = user.get('openid','')
                            wx_nickname = user.get('wx_nickname', '')
                            wx_img = user.get('wx_headimgurl', '')
                            if wx_img!='':
                                break
            else:
                if_bind = False
                openid = ''
                wx_nickname = ''
                wx_img = ''

            print '====> BIND: ', if_bind, wx_nickname.encode('utf-8'), wx_img.encode('utf-8')

            return json.dumps({
                'ret'  : 0,
                'data' : {
                    'session' : session['session_id'],
                    'login'   : True,
                    'addr'    : addr,
                    'uname'   : session['uname'],
                    # 'alert'   : alert,
                    'alert'   : False,  # 20170208产品要求关闭新用户注册送券弹框
                    'message' : message,
                    'openid'  : openid,
                    'wx_img'  : wx_img,
                    'wx_nickname': wx_nickname,
                    'if_bind': if_bind,
                    'pop_message' : pop_message,
                    'user_new' : user_new,
                }
            })
        else: # v1,v2
            return json.dumps({
                'ret'  : 0,
                'data' : {
                    'session' : session['session_id'],
                    'login'   : True,
                    'addr'    : addr,
                    'uname'   : session['uname'],
                }
            })
