#!/usr/local/bin/python
#-*- coding:utf-8 -*-

import httplib, urllib, time
from config import setting
import app_helper

db = setting.db_web


#服务地址
host = "www.jianzhou.sh.cn"
#端口号
port = 80
#短信接口的URI
send_uri = "/JianzhouSMSWSServer/http/sendBatchMessage" 
#账号
account  = "jzyy901"
#密码
psw = "123456"

# 建周科技
def send_sms(text, phone):
    params = urllib.urlencode({'account': account, 'password' : psw, 'msgText': text, 'destmobile':phone})
    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
    conn = httplib.HTTPConnection(host, port=port, timeout=30)
    conn.request("POST", send_uri, params, headers)
    response = conn.getresponse()
    response_str = response.read()
    conn.close()
    return response_str

# 检查发送频率
# 每小时可发送 10 次，每次间隔大于1分钟
def check_send_freq(mobile): 
    tick = int(time.time())
    r = db.sms_sent_log.find_one({'mobile':mobile})
    if r==None: 
        # 没发过
        db.sms_sent_log.insert_one({
            'mobile'    : mobile,
            'last_t'    : tick, # 最近一次 tick
            'history' : [app_helper.time_str()],
            'in_hour'   : tick, # 1小时计数 tick
            'n_in_hour' : 1,  # 1小时计数
        })
    else:
        if tick-r['last_t']<60: # 每次间隔大于1分钟
            print '短信 -------> ', mobile, '------> 1分钟内多次！'
            return False
        if tick-r['in_hour']<3600 and r['n_in_hour']>=10: # 1小时内发生不超过10次
            print '短信 -------> ', mobile, '------> 1小时内超过10次！'
            return False
        # 更新时间记录
        db.sms_sent_log.update_one({'mobile' : mobile},{
            '$set'  : {
                'last_t'    : tick,
                'in_hour'   : tick if tick-r['in_hour']>3600 else r['in_hour'],
                'n_in_hour' : 1 if tick-r['in_hour']>3600 else (r['n_in_hour']+1),
            },
            '$push' : {
                'history' : app_helper.time_str(), # 记录发送历史, 2017-06-28, gt
            },
        })
    return True

# 发验证码
def send_rand(mobile, rand, register=False):
    # 检查发送频率
    if not check_send_freq(mobile): 
        return None

    # 移动号码 ('134','135','136','137','138','139','150','151','152','157','158','159','187','188')

    print '短信 -------> ', mobile, '------>', rand

    if register:
        text = "感谢您注册预知来，您的验证码是%s【建周科技】" % rand
    else:
        text = "您的验证码是%s。如非本人操作，请忽略本短信【建周科技】" % rand
    r = send_sms(text, mobile) # 建周
    print r
    return r

