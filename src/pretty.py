#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import os, sys, gc
import time, json
from decimal import Decimal
from bson.objectid import ObjectId
from config.url import urls
from config import setting
from config.mongosession import MongoStore
import helper, app_helper
from libs import rand_code

from helper import time_str
from helper import get_privilege_name
from helper import logged
from helper import create_render

db = setting.db_web  # 默认db使用web本地
db_primary = setting.db_primary

app = web.application(urls, globals())
application = app.wsgifunc()

#--session---------------------------------------------------
web.config.session_parameters['cookie_name'] = 'herb_session'
web.config.session_parameters['secret_key'] = 'f6102bff8452386b8ca1'
web.config.session_parameters['timeout'] = 86400
web.config.session_parameters['ignore_expiry'] = True

if setting.debug_mode==False:
    ### for production
    session = web.session.Session(app, MongoStore(db_primary, 'sessions'), 
        initializer={'login': 0, 'privilege': 0, 'uname':'', 'uid':'', 'menu_level':''})
else:
    ### for staging,
    if web.config.get('_session') is None:
        session = web.session.Session(app, MongoStore(db_primary, 'sessions'), 
            initializer={'login': 0, 'privilege': 0, 'uname':'', 'uid':'', 'menu_level':''})
        web.config._session = session
    else:
        session = web.config._session

#----------------------------------------

# 在请求前检查helper.web_session, 调试阶段会出现此现象
def my_processor(handler): 
    if helper.web_session==None:
        print 'set helper.web_session'
        helper.set_session(session)     
    return  handler() 

app.add_processor(my_processor)
#----------------------------------------

gc.set_threshold(300,5,5)

user_level = helper.user_level

###########################################

def my_crypt(codestr):
    import hashlib
    return hashlib.sha1("sAlT139-"+codestr).hexdigest()


class Login:
    def GET(self):
        if logged():
            render = create_render()

            # 显示抽奖结果数量 2016-02-11， gt
            #result=os.popen('grep -c "=> 中奖" /usr/local/nginx/logs/backrun.log').readlines()
            #result = db.order_app.find({
            #   'status':{'$in':["PAID","DISPATCH","ONROAD","COMPLETE"]},
            #   "cart.0.product_id":{'$in':["1930001552","1930001551"]},
            #},{'order_id':1}).count()
            result = 0

            if logged(helper.PRIV_USER):
                # 提醒改密码
                db_user=db.user.find_one({'uname':session.uname},{'pwd_update':1})
                if int(time.time()) - db_user.get('pwd_update', 0) > 3600*24*30:
                    raise web.seeother('/settings_user?set_pwd=1')
                else:
                    return render.portal(session.uname, get_privilege_name(), [result])
            else:
                return render.portal(session.uname, get_privilege_name(), [result])
        else:
            render = create_render()

            db_sys = db.user.find_one({'uname':'settings'})
            if db_sys==None:
                signup=0
            else:
                signup=db_sys['signup']

            # 生成验证码
            rand=app_helper.my_rand(4).upper()
            session.uid = rand # uid 临时存放验证码
            session.menu_level = 0 # 暂存输入验证码次数
            png2 = rand_code.gen_rand_png(rand)

            return render.login(signup, png2)

    def POST(self):
        name0, passwd, rand = web.input().name, web.input().passwd, web.input().rand
        
        name = name0.lower()
        
        render = create_render()

        session.login = 0
        session.privilege = 0
        session.uname=''

        db_user=db.user.find_one({'uname':name},{'login':1,'passwd':1,'privilege':1,'menu_level':1,'pwd_update':1,'rand_fail':1})
        if db_user!=None and db_user['login']!=0:
            if session.menu_level>=5:
                print '-----> 刷验证码！'
                return render.login_error('验证码错误，请重新登录！')
            if session.uid != rand.upper():
                session.menu_level += 1
                return render.login_error('验证码错误，请重新登录！')
            if db_user['passwd']!=my_crypt(passwd):
                return render.login_error('密码错误，请重新登录！')

            session.login = 1
            session.uname = name
            session.uid = db_user['_id']
            session.privilege = int(db_user['privilege'])
            # 若是老用户则将session的权限位数增加至60
            session.menu_level = db_user['menu_level'] if len(db_user['menu_level']) == 60 else db_user['menu_level']+30*'-'
            raise web.seeother('/')
        else:
            return render.login_error()

class Reset:
    def GET(self):
        session.login = 0
        session.kill()
        render = create_render()
        return render.logout()

class SettingsUser:
    def _get_settings(self):
        db_user=db.user.find_one({'_id':session.uid},{'uname':1,'full_name':1})
        return db_user
    
    def GET(self):
        if logged(helper.PRIV_USER):
            render = create_render()
            if web.input(set_pwd='')['set_pwd']=='1':
                return render.settings_user(session.uname, get_privilege_name(), self._get_settings(), '请重新设置密码')
            else:
                return render.settings_user(session.uname, get_privilege_name(), self._get_settings())
        else:
            raise web.seeother('/')

    def POST(self):
        if logged(helper.PRIV_USER):
            render = create_render()
            #full_name = web.input().full_name
            old_pwd = web.input().old_pwd.strip()
            new_pwd = web.input().new_pwd.strip()
            new_pwd2 = web.input().new_pwd2.strip()
            
            if old_pwd!='':
                if new_pwd=='':
                    return render.info('新密码不能为空！请重新设置。')
                if new_pwd!=new_pwd2:
                    return render.info('两次输入的新密码不一致！请重新设置。')
                # 检查密码强度
                _num = 0
                _upper = 0
                _misc = 0
                for xx in new_pwd:
                    if xx.isdigit():
                        _num = 1
                    elif xx.isupper():
                        _upper = 1
                    elif xx in '+-_/%$':
                        _misc = 1
                if _num+_upper+_misc<3:
                    return render.info('密码强度太低，容易被破解，请重新输入！')

                db_user=db.user.find_one({'_id':session.uid},{'passwd':1})
                if my_crypt(old_pwd)==db_user['passwd']:
                    db.user.update_one({'_id':session.uid}, {'$set':{
                        'passwd'     : my_crypt(new_pwd),
                        'pwd_update' : int(time.time()),
                        #'full_name'  : full_name
                    }})
                else:
                    return render.info('登录密码验证失败！请重新设置。')
            #else:
            #   db.user.update_one({'_id':session.uid}, {'$set':{'full_name':full_name}})

            return render.info('成功保存！','/')
        else:
            raise web.seeother('/')



########## Admin 功能 ####################################################

class AdminUser:
    def GET(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()

            users=[]            
            db_user=db.user.find({'privilege': {'$nin': [helper.PRIV_ADMIN]}},
                    {'uname':1,'privilege':1,'full_name':1,'login':1}).sort([('_id',1)])
            if db_user.count()>0:
                for u in db_user:
                    if u['uname']=='settings':
                        continue
                    users.append([u['uname'],u['_id'],int(u['privilege']),u['full_name'],u['login']])
            return render.user(session.uname, user_level[session.privilege], users)
        else:
            raise web.seeother('/')


class AdminUserSetting:     
    def GET(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            user_data=web.input(uid='')

            if user_data.uid=='':
                return render.info('错误的参数！')  
            
            db_user=db.user.find_one({'_id':ObjectId(user_data.uid)})
            if db_user!=None:
                db_shop=db.base_shop.find({'available':1, 'type':{'$in':['chain','store','dark','virtual','pt_house']}}, {'name':1,'type':1})
                shops = []
                for s in db_shop:
                    shops.append((s['_id'], s['name'], helper.SHOP_TYPE[s['type']]))
                # 若是老用户，则在其menu_level位数的基础上增加至60位权限位
                new_menu_level = db_user['menu_level'] if len(db_user['menu_level']) == 60 else db_user['menu_level']+30*'-'
                return render.user_setting(session.uname, user_level[session.privilege], 
                    db_user, time_str(db_user['time']), 
                    get_privilege_name(db_user['privilege'],new_menu_level), shops)
            else:
                return render.info('错误的参数！')  
        else:
            raise web.seeother('/')

    def POST(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            user_data=web.input(uid='', shop='', shop2='', full_name='', passwd='', priv=[])

            shop=''
            privilege = helper.PRIV_USER
            menu_level = 60*'-'
            for p in user_data.priv:
                pos = helper.MENU_LEVEL[p]
                menu_level = menu_level[:pos]+'X'+menu_level[pos+1:]
                if p=='DELVERY_ORDER':
                    privilege |= helper.PRIV_DELIVERY
                if p in ['DELVERY_ORDER','POS_POS','POS_INVENTORY','ONLINE_MAN',
                    'POS_AUDIT','POS_REPORT','POS_PRINT_LABEL','POS_REPORT_USER']:
                    if user_data.shop=='':
                        return render.info('请选择门店！')
                    else:
                        shop = ObjectId(user_data.shop)

            # 更新数据
            update_set = {'$set':{
                'login'  : int(user_data['login']), 
                'privilege' : privilege, 
                'menu_level': menu_level,
                'full_name' : user_data['full_name'],
                'shop'    : shop
            }}

            # 如需要，更新密码
            if len(user_data['passwd'])>0:
                update_set['$set']['passwd']=my_crypt(user_data['passwd'])
                update_set['$set']['pwd_update']=0

            db.user.update_one({'_id':ObjectId(user_data['uid'])}, update_set)

            return render.info('成功保存！','/admin/user')
        else:
            raise web.seeother('/')

class AdminUserAdd:     
    def GET(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            db_shop=db.base_shop.find({'available':1, 'type':{'$in':['chain','store','dark','pt_house','virtual']}}, {'name':1,'type':1})
            shops = []
            for s in db_shop:
                shops.append((s['_id'], s['name'], helper.SHOP_TYPE[s['type']]))
            return render.user_new(session.uname, user_level[session.privilege],shops)
        else:
            raise web.seeother('/')

    def POST(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            user_data=web.input(uname='', login='0', passwd='', shop='', shop2='', full_name='', priv=[])
            print user_data

            if user_data.uname=='':
                return render.info('用户名不能为空！')  
            
            db_user=db.user.find_one({'uname': user_data['uname']})
            if db_user==None:
                shop = ''
                privilege = helper.PRIV_USER
                menu_level = 60*'-'
                for p in user_data.priv:
                    pos = helper.MENU_LEVEL[p]
                    menu_level = menu_level[:pos]+'X'+menu_level[pos+1:]
                    #if p=='DELVERY_ORDER':
                    #   privilege |= helper.PRIV_DELIVERY
                    #if p in ['DELVERY_ORDER','POS_POS','POS_INVENTORY','ONLINE_MAN',
                    #   'POS_AUDIT','POS_REPORT','POS_PRINT_LABEL','POS_REPORT_USER']:
                    #   if user_data.shop=='':
                    #       return render.info('请选择门店！')
                    #   else:
                    #       shop = ObjectId(user_data.shop)

                db.user.insert_one({
                    'login'  : int(user_data['login']),
                    'uname'  : user_data['uname'],
                    'full_name' : user_data['full_name'],
                    'privilege' : privilege,
                    'menu_level': menu_level,
                    #'shop'   : shop,
                    'passwd'    : my_crypt(user_data['passwd']),
                    'time'    : time.time()  # 注册时间
                })
                return render.info('成功保存！','/admin/user')
            else:
                return render.info('用户名已存在！请修改后重新添加。')
        else:
            raise web.seeother('/')

class AdminSysSetting:      
    def GET(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
    
            db_sys=db.user.find_one({'uname':'settings'})
            if db_sys!=None:
                return render.sys_setting(session.uname, user_level[session.privilege], db_sys)
            else:
                db.user.insert_one({'uname':'settings','signup':0,'login':0,
                'pk_count':1,'wt_count':1,'sa_count':1})
                return render.info('如果是新系统，请重新进入此界面。','/')  
        else:
            raise web.seeother('/')

    def POST(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            user_data=web.input(signup='0', pk_count='1', wt_count='1', sa_count='1')

            db.user.update_one({'uname':'settings'},{'$set':{
                'pk_count': int(user_data['pk_count']),
                'wt_count': int(user_data['wt_count']),
                'sa_count': int(user_data['sa_count']),
            }})

            return render.info('成功保存！','/admin/sys_setting')
        else:
            raise web.seeother('/')

class AdminSelfSetting:

    def _get_settings(self):
        db_user=db.user.find_one({'_id':session.uid})
        return db_user

    def GET(self):
        #print web.ctx
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            return render.self_setting(session.uname, user_level[session.privilege], self._get_settings())
        else:
            raise web.seeother('/')

    def POST(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
            old_pwd = web.input().old_pwd.strip()
            new_pwd = web.input().new_pwd.strip()
            new_pwd2 = web.input().new_pwd2.strip()
    
            if old_pwd!='':
                if new_pwd=='':
                    return render.info('新密码不能为空！请重新设置。')
                if new_pwd!=new_pwd2:
                    return render.info('两次输入的新密码不一致！请重新设置。')
                db_user=db.user.find_one({'_id':session.uid},{'passwd':1})
                if my_crypt(old_pwd)==db_user['passwd']:
                    db.user.update_one({'_id':session.uid}, {'$set':{'passwd':my_crypt(new_pwd)}})
                    return render.info('成功保存！','/')
                else:
                    return render.info('登录密码验证失败！请重新设置。')
            else:
                return render.info('未做任何修改。')
        else:
            raise web.seeother('/')

class AdminStatus: 
    def GET(self):
        import os

        if logged(helper.PRIV_ADMIN):
            render = create_render()
        
            uptime=os.popen('uptime').readlines()
            takit=os.popen('pgrep -f "uwsgi_fair.sock"').readlines()
            error_log=os.popen('tail %s/error.log' % setting.logs_path).readlines()
            uwsgi_log=os.popen('tail %s/uwsgi_fair.log' % setting.logs_path).readlines()
            processor_log=os.popen('tail %s/processor.log' % setting.logs_path).readlines()
            df_data=os.popen('df -h').readlines()

            #import sms_mwkj
            #balance = sms_mwkj.query_balance()

            return render.status(session.uname, user_level[session.privilege],{
                'uptime'       :  uptime,
                'takit'     :  takit,
                'error_log' :  error_log,
                'uwsgi_log' :  uwsgi_log,
                'process_log'  :  processor_log,
                'df_data'     :  df_data})
        else:
            raise web.seeother('/')

class AdminData: 
    def GET(self):
        if logged(helper.PRIV_ADMIN):
            render = create_render()
    
            db_active=db.user.find({'$and': [{'login'    : 1},
                             {'privilege' : helper.PRIV_USER},
                            ]},
                            {'_id':1}).count()
            db_nonactive=db.user.find({'$and': [{'login'     : 0},
                             {'privilege' : helper.PRIV_USER},
                            ]},
                            {'_id':1}).count()
            db_admin=db.user.find({'privilege' : helper.PRIV_ADMIN}, {'_id':1}).count()

            db_sessions=db.sessions.find({}, {'_id':1}).count()
            db_device=db.device.find({}, {'_id':1}).count()
            db_todo=db.todo.find({}, {'_id':1}).count()
            db_sleep=db.todo.find({'status':'SLEEP'}, {'_id':1}).count()
            db_lock=db.todo.find({'lock':1}, {'_id':1}).count()
            db_thread=db.thread.find({}).sort([('tname',1)])
            idle_time = []
            for t in db_thread:
                idle_time.append(t)

            return render.data(session.uname, user_level[session.privilege],
                {
                  'active'     :  db_active,
                  'nonactive'   :  db_nonactive,
                  'admin'       :  db_admin,
                  'sessions'     :  db_sessions,
                  'device'     :  db_device,
                  'todo'         :  db_todo,
                  'sleep'       :  db_sleep,
                  'lock'         :  db_lock,
                  'idle_time'   :  idle_time,
                })
        else:
            raise web.seeother('/')


#if __name__ == "__main__":
#   web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#   app.run()
