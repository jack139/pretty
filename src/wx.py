#!/usr/bin/env python
# -*- coding: utf-8 -*-

import web
import time, json, urllib, urllib2, urllib3, datetime, hashlib
import gc
from config.url_wx import urls
from config import setting
import app_helper
from app_helper import time_str, get_token
from libs import app_user_helper

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

db = app_helper.db  # 默认db使用web本地

app = web.application(urls, globals())
application = app.wsgifunc()

gc.set_threshold(300,5,5)

# 微信设置
wx_appid=setting.wx_setting['wx_appid']
wx_secret=setting.wx_setting['wx_appsecret']


REFRESH_HEADIMG = 10 # 更用户头像的频次
  
##############################################

def create_render(plain=False):    
    if plain: layout=None
    else: layout='layout'
    render = web.template.render('templates/wx', base=layout)
    return render

def check_wx_user(wx_user):
    db_wx=db.wx_user.find_one({'wx_user':wx_user},{'owner':1})
    if db_wx!=None: # 已登记
        return db_wx['owner']
    else: # 未登记
        db.wx_user.insert_one({'wx_user' : wx_user, 'owner': '', 'time' : time_str()})
        return ''

def bind_wx_user(wx_user, fair_user):
    # 关注时， fair_user 为region_id
    # 取消关注时，fair_user 为 'N/A'
    check_wx_user(wx_user)
    if fair_user=='N/A':
        push_data = 'unsubscribe'
    else:
        push_data = 'subscribe'
    db.wx_user.update_one({'wx_user':wx_user},{
        '$set'  : { 'owner':fair_user, 'last_tick': int(time.time()) },
        '$push' : { 'history' : (time_str(), push_data, fair_user) },
    })

def reply_none():
    web.header("Content-Type", "text/plain") # Set the Header
    return ""

# 判断是否已关注公众号
def openid_is_fun(openid):
    db_wx=db.wx_user.find_one({'wx_user':openid},{'owner':1})
    if db_wx!=None and db_wx['owner']!='N/A':
        return True
    else:
        return False


#回复配置文件处理
def get_reply_json():
    from libs import reply_conf

    json_data = reply_conf.json_file

    return json_data['text'], json_data['media']


g_text_json, g_media_json = get_reply_json()

class PostMsg:
    def __init__(self, str_xml):
        # <EventKey><![CDATA[qrscene_123]]></EventKey>
        self.xml=ET.fromstring(str_xml)
        self.fromUser=self.xml.find("FromUserName").text
        self.toUser=self.xml.find("ToUserName").text
        self.msgType=self.xml.find("MsgType").text
        self.key=''
        self.str_xml = str_xml
        print str_xml
    
    def reply_text(self, content):
        render = create_render(plain=True)
        return render.xml_reply(self.fromUser, self.toUser, int(time.time()), content)

    def reply_media(self, content):
        # 标题，说明，图片url，页面url
        #content = [(u'标题2', u'', u'', u'http://wx.f8geek.com/live2')]
        render = create_render(plain=True)
        return render.xml_media(self.fromUser, self.toUser, int(time.time()), content)      

    def start_mul_service(self):
        render = create_render(plain=True)
        return render.mul_service(self.fromUser,self.toUser,int(time.time()))

    def is_service_time(self):
        time_now = datetime.datetime.now().time()
        if time_now < datetime.time(hour=21) and time_now > datetime.time(hour=8):
            return True
        else:
            return False

    def get_text_reply(self, content_text):
        global g_text_json
        
        if content_text in g_text_json.keys():
            return g_text_json.get(content_text, None)
        
        return None

    def get_media_reply(self, content_text):
        global g_media_json
        
        if content_text in g_media_json.keys():
            return g_media_json.get(content_text, None)
        
        return None
    def text_process(self): # 处理文本消息回复
        content=self.xml.find("Content").text
        cmd0 = content.split()
        content_text = cmd0[0].lower()
        print 'AAAAAAAAAAAAAAAAAAAA'
        print setting.region_id

        if '0' == content_text and self.is_service_time() and setting.region_id in ['003','000']:
            #开启客服接口
            return self.start_mul_service()
            
        #if u'分销商' in content_text: # 分销商
        #    return self.reply_media([
        #        (u'分销中心入口',u'',u'',
        #        u'http://%s/wx/init_distribution'%setting.wx_host)
        #    ])
            
        text_res = self.get_text_reply(content_text)
        if text_res != None:
            return self.reply_text(text_res)

        media_res = self.get_media_reply(content_text)
        if media_res != None:
            return self.reply_media(media_res)
            
        text_res = self.get_text_reply('main_reply')
        if text_res != None:
            return self.reply_text(text_res)
        return self.reply_text(u"联系客服请输入0")

    def media_process(self): # 处理文本消息回复
        if  self.is_service_time():
            #开启客服接口
            return self.start_mul_service()
        return self.reply_text(u"联系客服请输入0")

    def event_process(self): # 处理事件请求
        event=self.xml.find("Event").text
        if event=='CLICK':
            self.key=self.xml.find("EventKey").text
            #print self.key
            if self.key=='CLICK_WAIT':
                return self.reply_text(u"敬请期待！")
            elif self.key=='CLICK_SERVICE':
                if not self.is_service_time():
                    return self.reply_text(u"亲爱的客官，感谢您关注。在线客服服务每天8:00-21:00真人值守，全心全意为您服务！请客官概述一下您遇到的问题，我们将对应问题安排客服快速、有效的帮助您，谢谢")
                else:
                    return self.start_mul_service()
            elif self.key=='CLICK_SUGGEST':
                return self.reply_text(u"谢谢您对我们的支持。在下方聊天框中输入“我有建议+您的建议+姓名+联系电话”即可。我们会认真考虑您的每一个宝贵的意见和建议，我们会在您的帮助下做得越来越好，再次感谢您的支持。")
        elif event=='subscribe':
            #print "NEW: %s" % self.fromUser
            bind_wx_user(self.fromUser, setting.region_id)

            # 获取 ticket，如果有，要建立分销关系
            self.key=self.xml.find("EventKey").text
            self.ticket=self.xml.find("Ticket")
            #print '%r, %r'%(self.key, self.ticket)
            if self.ticket!=None:
                ticket = self.ticket.text
                openid = self.fromUser

                print 'ticket ====>', ticket
                print {'QR_info.ticket':ticket}

                r9 = db.fx_root.find_one({'QR_info.ticket':ticket},{'root':1})
                if r9: # 存在ticket

                    parent_u = r9['root']

                    #db_user = db.app_user .find_one({'openid':openid})
                    db_user = app_user_helper.get_user_info(openid, q_type='openid')
                    if db_user == None: # 新用户才建立分销关系

                        # 用户基本信息
                        info = get_info(openid)
                        if info.has_key('errcode'):
                            get_ticket(True)
                            info = get_info(openid)
                        print info

                        unionid = info.get('unionid','')

                        #db.app_user .insert_one({
                        new_set = {
                            'openid'   : openid,
                            'unionid'  : unionid,
                            'region_id': setting.region_id, # 增加 region_id
                            'type'     : 'wx_pub', # 用户类型
                            'address'  : [],
                            'coupon'   : [], # 送优惠券
                            'app_id'   : '', # 微信先注册，没有app_id
                            'reg_time' : app_helper.time_str(),
                            'wx_nickname'   : info.get('nickname','游客'),
                            'wx_headimgurl' : info.get('headimgurl', ''),
                            'wx_info'       : info,
                            'refresh_headimg' : REFRESH_HEADIMG, 
                            'last_status' : int(time.time()),
                        }

                        # 用户中心注册用户接口
                        app_user_helper.new_user_info(openid, 'openid', new_set)

                        # 添加用户关系 2016-03-31
                        # 只有新注册用户添加
                        from libs import user_tree
                        print 'parent_u', parent_u, unionid
                        if parent_u!=None and unionid!=parent_u:
                            user_tree.add_parent(unionid, parent_u)
                            print '======> TREE:', unionid, parent_u

            #return self.reply_text(u"欢迎使用微信服务号！")

            text_res = self.get_text_reply('main_reply')
            if text_res != None:
                return self.reply_text(text_res)
            

        elif event=='unsubscribe':
            #print "LEFT: %s" % self.fromUser
            bind_wx_user(self.fromUser, 'N/A')
        return reply_none()

    def do_process(self):
        if self.msgType=='text':
            return self.text_process()
        elif self.msgType=='image' or self.msgType=='voice':
            return self.media_process()
        elif self.msgType=='event':
            return self.event_process()
        else:
            return reply_none()
    
        
class First:
    def GET(self):
#       test1='<xml><ToUserName><![CDATA[gh_96ef24d64c49]]></ToUserName>' \
#           '<FromUserName><![CDATA[ogQxxuBJi1KR_BLn86aRIKTHrcPM]]></FromUserName>' \
#           '<CreateTime>1411443827</CreateTime>' \
#           '<MsgType><![CDATA[event]]></MsgType>' \
#           '<Event><![CDATA[CLICK]]></Event>' \
#           '<EventKey><![CDATA[KAM_SNAPSHOT]]></EventKey>' \
#           '</xml>'
#       pm=PostMsg(test1)
#       return pm.do_process()

        user_data=web.input(signature='', timestamp='', nonce='', echostr='')
        if '' in (user_data.signature, user_data.timestamp, user_data.nonce, user_data.echostr):
            return reply_none()

        token1='7a710d7955acb49fbf1a'  # hashlib.sha1('ilovekam').hexdigest()[5:25]
        tmp=[token1, user_data.timestamp, user_data.nonce]
        tmp.sort()
        tmp1=tmp[0]+tmp[1]+tmp[2]
        tmp2=hashlib.sha1(tmp1).hexdigest()
        #print "%s %s %s" % (tmp1, tmp2, user_data.signature)
        
        web.header("Content-Type", "text/plain") # Set the Header
        if tmp2==user_data.signature:
            return user_data.echostr
        else:
            return "fail!"

    def POST(self):
        user_data=web.input(signature='', timestamp='', nonce='')
        if '' in (user_data.signature, user_data.timestamp, user_data.nonce):
            return reply_none()
        
        token1='7a710d7955acb49fbf1a'  # hashlib.sha1('ilovekam').hexdigest()[5:25]
        tmp=[token1, user_data.timestamp, user_data.nonce]
        tmp.sort()
        tmp1=tmp[0]+tmp[1]+tmp[2]
        tmp2=hashlib.sha1(tmp1).hexdigest()

        if tmp2!=user_data.signature:
            return reply_none()

        #从获取的xml构造xml dom树
        str_xml=web.data()
        
        #print str_xml
        
        pm=PostMsg(str_xml)
        return pm.do_process()

# 获取ticket
def get_ticket(force=False): # force==True 强制刷新
    if not force:
        db_ticket = db.jsapi_ticket.find_one({'region_id':setting.region_id})
        if db_ticket and int(time.time())-db_ticket.get('tick', 0)<3600:
            if db_ticket.get('ticket', '')!='':
                print db_ticket['ticket']
                return db_ticket['ticket']

    token = get_token(force)
    url='https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token=%s&type=jsapi' % token
    f=urllib.urlopen(url)
    data = f.read()
    f.close()

    print '#########################get_ticket get_ticket'
    print data
    t=json.loads(data)
    if t.has_key('ticket'):
        #print t
        db.jsapi_ticket.update_one({'region_id':setting.region_id},
            {'$set':{'tick':int(time.time()), 'ticket':t['ticket']}},upsert=True)
        return t['ticket']
    else:
        db.jsapi_ticket.update_one({'region_id':setting.region_id},
            {'$set':{'tick':int(time.time()), 'ticket':''}},upsert=True)
        return ''

# 获取用户基本信息
def get_info(openid):
    token = get_token()
    url='https://api.weixin.qq.com/cgi-bin/user/info?access_token=%s&openid=%s&lang=zh_CN' % (token, openid)
    f=urllib.urlopen(url)
    data = f.read()
    f.close()

    print data
    try:
        t=json.loads(data)
    except ValueError:
        t={'errcode':999}
    return t

# 微信入口
def get_redirect_loc(redirect_uri):
    #redirect_uri = 'http://wx-test.urfresh.cn/wx/fair'
    loc =   'https://open.weixin.qq.com/connect/oauth2/authorize?' \
        'appid=%s&' \
        'redirect_uri=%s&' \
        'response_type=code&' \
        'scope=snsapi_base&' \
        'state=1#wechat_redirect' % (wx_appid, urllib.quote_plus(redirect_uri))
    return loc

# 店铺入口， 测试 http://wx-test.urfresh.cn/wx/fair?code=test
def init_job(code, need_more_data=False, parent=None):
    if code=='':
        #return render.info('参数错误',goto='/') # info页面要做微信端优化
        #raise web.seeother('/wx/init_fair')
        if need_more_data:
            return None, None, 0, 0
        else:
            return None

    if code=='test':
        openid = code
    else:
        urllib3.disable_warnings()
        http = urllib3.PoolManager(num_pools=2, timeout=180, retries=False)
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token?' \
            'appid=%s&' \
            'secret=%s&' \
            'code=%s&' \
            'grant_type=authorization_code' % \
            (wx_appid, wx_secret, code, )
        r = http.request('GET', url)
        if r.status==200:
            data = r.data
            t=json.loads(data)
            #print t

            http.clear()

            if t.has_key('openid'):
                openid = t['openid']
            else:
                #print '===========Error==============', data, wx_secret, wx_appid
                if need_more_data:
                    return None, None, 0, 0
                else:
                    return None
        else:
            http.clear()

            if need_more_data:
                return None, None, 0, 0
            else:
                return None

    # 取得ticket
    ticket = get_ticket()
    if ticket=='':
        print 'get ticket fail!'
        #raise web.seeother('/wx/init_fair')
        #return None
        ticket = get_ticket(True)

    uname = ''

    # 检查用户是否已注册
    #db_user = db.app_user .find_one({'openid':openid})
    db_user = app_user_helper.get_user_info(openid, q_type='openid')
    is_new_user = 0
    is_our_fan = True
    if db_user==None:
        # 未注册，新建用户记录
        is_new_user = 1
        # 用户基本信息
        info = get_info(openid)
        if info.has_key('errcode'):
            get_ticket(True)
            info = get_info(openid)
        print info

        unionid = info.get('unionid','')

        coupon = []
        #valid = app_helper.time_str(time.time()+3600*24*10, 1) # 有效期10天 2015-11-22
        # 注册发抵用券 v3 ----- 不发了 2015-11-28
        #for i in app_helper.reginster_coupon:
        #   coupon.append((app_helper.my_rand(), valid, '%.2f' % float(i[0]), 1, i[1], i[2]))
        #db.app_user .insert_one({
        new_set = {
            'openid'   : openid,
            'unionid'  : unionid,
            'region_id': setting.region_id, # 增加 region_id
            'type'     : 'wx_pub', # 用户类型
            'address'  : [],
            'coupon'   : coupon, # 送优惠券
            'app_id'   : '', # 微信先注册，没有app_id
            'reg_time' : app_helper.time_str(),
            'wx_nickname'   : info.get('nickname','游客'),
            'wx_headimgurl' : info.get('headimgurl', ''),
            'wx_info'       : info,
            'refresh_headimg' : REFRESH_HEADIMG, 
            'last_status' : int(time.time()),
            'app_order_num': 0  # 20160927 lf 未下单
        }
        # 用户中心注册用户接口
        app_user_helper.new_user_info(openid, 'openid', new_set)

        is_our_fan = not (info.get('nickname',u'游客')==u'游客') # 是否是公众号粉丝，通过是否是游客判断

        # 添加用户关系 2016-03-31
        # 只有新注册用户添加
        if parent not in [None, '']:
            from libs import user_tree
            parent_u = user_tree.owner2unionid(parent)
            if parent_u!=None and unionid!=parent_u:
                user_tree.add_parent(unionid, parent_u)
                print '======> TREE:', unionid, parent_u

    else:
        # 记录今天访问次数
        last_date = db_user.get('last_visit_date')
        today_date = app_helper.time_str(format=1)  # 格式 2016-01-01
        if last_date!=today_date:
            update_set = {
                'last_visit_date' : today_date,
                'today_visit_count' : 1,
                'todat_visit_first_tick' : int(time.time()),
                'todat_push_image_text' : 0,
            }
        else:
            update_set = {
                'today_visit_count' : db_user.get('today_visit_count',0) + 1,
            }

        # 更新 region_id
        if db_user.get('region_id')!=setting.region_id:
            update_set['region_id'] = setting.region_id

        if not openid_is_fun(openid) \
            or db_user.get('wx_nickname', '')=='' \
            or db_user.get('refresh_headimg',0)<=0: # 没有关注

            # 用户基本信息
            info = get_info(openid)
            if info.has_key('errcode'):
                get_ticket(True)
                info = get_info(openid)
            print info

            unionid = info.get('unionid','')

            # 补充微信用户信息
            
            update_set['unionid']         = unionid
            update_set['wx_nickname']     = info.get('nickname','游客')
            update_set['wx_headimgurl']   = info.get('headimgurl', '')
            update_set['wx_info']         = info
            update_set['refresh_headimg'] = REFRESH_HEADIMG

            #db.app_user .update_one({'openid':openid}, {'$set': update_set})
            app_user_helper.update_user_info(openid, q_type='openid', update_set=update_set)
            is_our_fan = not (info.get('nickname',u'游客')==u'游客')
        else:
            unionid = db_user.get('unionid','')
            is_our_fan = True
            # 刷新refresh_headimg
            db.app_user.update_one({'openid':openid}, 
                {
                    '$set': update_set,
                    '$inc': {'refresh_headimg' : -1}
                }
            )

        uname = db_user.get('uname','')


        # 添加用户关系 2016-03-31
        # 已注册用户添加 ================================  仅测试用 ======
        #if parent not in [None, '']:
        #    from libs import user_tree
        #    parent_u = user_tree.owner2unionid(parent)
        #    if parent_u!=None and unionid!=parent_u:
        #        user_tree.add_parent(unionid, parent_u)
        #        print '======> TREE:', unionid, parent_u
        #==============================================================

    # 更新 unionid_index, 2016-03-01 , gt
    #db.unionid_index .update_one({'openid':openid}, {'$set':{'unionid':unionid}}, upsert=True)
    app_user_helper.update_unionid_info(openid, 'openid', {'unionid':unionid})

    # 生成 session ------------------

    rand2 = app_helper.my_rand(16)
    now = time.time()
    secret_key = 'f6102bff8451236b8ca1'
    session_id = hashlib.sha1("%s%s%s%s" %(rand2, now, web.ctx.ip.encode('utf-8'), secret_key))
    session_id = session_id.hexdigest()

    db.app_sessions.insert_one({
        'session_id' : session_id,
        'openid'     : openid,
        'unionid'    : unionid,
        'ticket'     : ticket,
        'uname'      : uname,
        'login'      : 1,
        'rand'       : rand2,
        'ip'         : web.ctx.ip,
        'attime'     : now,
        'type'       : 'wx',
    })

    print session_id, openid, uname
    print "qqffdd session_id >>>>>>>>>> %r" %session_id
    if need_more_data: # 返回是否是粉丝
        return session_id, is_our_fan, is_new_user, openid
    else:
        return session_id

#------------------------------------------------
'''
herb.html       /wx/init_fair 
user_info.html       /wx/init_user_info
'''

def get_param(url_param): # 保持所有的参数，除了code和state
    print url_param
    param_0 = dict(url_param)
    param_0.pop('code',None)
    param_0.pop('state',None)
    param_0.pop('region_id',None)
    param_0.pop('session_id',None)
    #print param_0
    #param = '&'.join(['%s=%s'%(i,urllib.quote_plus(param_0[i].encode('utf-8'))) for i in param_0.keys()])
    param = '&'.join(['%s=%s'%(i,param_0[i]) for i in param_0.keys()])
    #if len(param)>0:
    #    param += '&region_id=%s'%setting.region_id # 固定都加 region_id
    #else:
    #    param = 'region_id=%s'%setting.region_id # 固定都加 region_id
    return param

#------------------------------------------------
# 下单入口
class InitHerb: # fair.html
    def GET(self):
        param = get_param(web.input())
        raise web.redirect(get_redirect_loc('http://%s/wx/herb_init?%s' % (setting.wx_host, param)))

class Herb: 
    def GET(self):
        return self.POST()

    def POST(self):
        user_data=web.input(code='')
        param = get_param(user_data)
        if user_data.get('session_id','')=='':
            session_id = init_job(user_data.code)
            if session_id==None:
                raise web.seeother('/wx/init_herb?%s' % param)
        else:
            session_id = user_data['session_id']
        #render = create_render(plain=True)
        #return render.fair(session_id, HTML_SETTING[setting.region_id], param)
        print '/static/wx/index.html?session_id=%s&%s' % (session_id, param)
        raise web.seeother('/static/wx/index.html?session_id=%s&%s' % (session_id, param))

#------------------------------------------------
# 我的用户信息
class InitUserInfo: # userInfo.html
    def GET(self):
        param = get_param(web.input())
        raise web.redirect(get_redirect_loc('http://%s/wx/user_info_init?%s' % (setting.wx_host, param)))

class UserInfo:
    def GET(self):
        return self.POST()

    def POST(self):
        user_data=web.input(code='', owner='')
        param = get_param(user_data)
        if user_data.get('session_id','')=='':
            session_id = init_job(user_data.code, parent=user_data['owner'])
            if session_id==None:
                raise web.seeother('/wx/init_user_info?%s' % param)
        else:
            session_id = user_data['session_id']
        #render = create_render(plain=True)
        #return render.userInfo(session_id, HTML_SETTING[setting.region_id], param)
        #raise web.seeother('/static/wx/user_info.html?session_id=%s&%s' % (session_id, param))
        print '/static/wx/index.html?session_id=%s&%s#/base/center' % (session_id, param)
        raise web.seeother('/static/wx/index.html?session_id=%s&%s#/base/center' % (session_id, param))

#------------------------------------------------

class WxSignature:
    def POST(self):
        web.header('Content-Type', 'application/json')
        param = web.input(currUrl='',cross='', share_type='')
        ticket = get_ticket()
        if ticket=='':
            # 重试一次
            ticket = get_ticket()
            if ticket=='':
                print '---------- get ticket fail!'
                #return None

        noncestr = app_helper.my_rand()
        timestamp = str(int(time.time()))
        #url = 'http://test.urfresh.cn/static/hb/001.html'
        url = param.currUrl
        string1 = 'jsapi_ticket=%s&noncestr=%s&timestamp=%s&url=%s' % (ticket, noncestr, timestamp, url)

        print string1

        if param.cross=='yes':
            return 'jsonpcallback(%s)' % json.dumps({
                'appid'     : wx_appid,
                'timestamp' : timestamp,
                'nonceStr'  : noncestr,
                'sign'      : hashlib.sha1(string1).hexdigest(),
            })
        else:
            return json.dumps({
                'appid'     : wx_appid,
                'timestamp' : timestamp,
                'nonceStr'  : noncestr,
                'sign'      : hashlib.sha1(string1).hexdigest(),
            })

    def GET(self):
        return self.POST()


#if __name__ == "__main__":
#    web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
#    app.run()
