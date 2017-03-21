#!/usr/bin/env python
# -*- coding: utf-8 -*-

from config import setting
import gc,sys
import threading
import  time, json, random
import traceback
import app_helper 
from libs import log4u

db = setting.db_primary

DEALY=10

# ---------------------------------------

def update_event_status(event_id, status, msg=''):
    return db.event_queue.update_one({'_id':event_id},{
        '$set'  : {'status':status, 'lock':0},
        '$inc'  : {'count':1},
        '$push' : {'history':(app_helper.time_str(), msg)}
    })

# ---------------------------------------

def send_wx_msg(r):
    r0 = app_helper.wx_reply_msg(
        r['data']['openid'],
        r['data']['text'],
        r['data']['region_id']
    )
    if r0==None or r.get('errcode', 0)!=0:
        print '推送失败：', str(r['_id'])
        status='FAIL'
    else:
        status='DONE'

    return status, ''





# 清理过期和长时间不用的session
def refresh_session_timeout():
    now = int(time.time())
    # 修改为付款的过期订单
    r6 = db.order_app.find({
        #'uname'    : {'$in':unionid_helper.all_ids(uname)},
        'status'   : 'DUE',
        'deadline' : {'$lt':now}
    }, {'order_id':1})
    # logging
    for yy in r6:
        log4u.log('backrun', log4u.TIMEOUT , '过期未付款', yy['order_id'])

    r5 = db.order_app.update_many({
        #'uname'    : {'$in':unionid_helper.all_ids(uname)},
        'status'   : 'DUE',
        'deadline' : {'$lt':now}
    }, {'$set': {
        'status'     : 'TIMEOUT',
        'TIMEOUT'    : int(time.time()), # 2016-01-10, gt
        'last_status': int(time.time()), 
    }})


    #if r5.modified_count>0: print 'TIMEOUT: ', r5.raw_result

    #清理 TIMEOUT 订单, 30天前的
    #r5=db.order_app.delete_many({'status':'TIMEOUT','deadline' : {'$lt':now-3600*24*30}})
    # 清理 session, 24小时前的微信session
    r5=db.app_sessions.delete_many({'type':'wx','attime':{'$lt':(now-3600*24)}})
    #if r5.deleted_count>0: print 'wx session: ', r5.raw_result
    # 清理 session, 12小时前的未登录的session
    r5=db.app_sessions.delete_many({'login':0,'attime':{'$lt':(now-3600*12)}})
    #if r5.deleted_count>0: print 'unlogin session: ', r5.raw_result
    # 清理 session, 30天前的未使用的session
    r5=db.app_sessions.delete_many({'attime':{'$lt':(now-3600*24*30)}})
    #if r5.deleted_count>0: print '10days old: ',r5.raw_result



#
# 事件表
#
#event_queue
#{
#    'type' : 'WX_MSG', # 'WX_MSG', 'SMS_MSG', 'JPUSH_MSG'
#    'data' : {
#        'text'     : '',
#        'orgion'   : '',
#        'url'      : '',
#        'region_id': '',
#    }
#    'status' : 'WAIT', # 'WAIT', 'DONE'
#    'lock' : 0,
#}
#   
#   WX_MSG
#
def check_event(tname, tid):
    '''查询数据库中的所有数据'''
        
    if tid!=0: # 其他线程不进行退款，避免大量退款占用所用线程，影响推单
        r = db.event_queue.find_one_and_update(
            {'$and': [
                    {'lock'   : {'$ne':1}},
                    {'status' : 'WAIT'},
                    #{'type'   : {'$nin':['REFUND_CRE', 'REFUND_WX','REFUND_CRE2','WX_MSG','WX_AFT_46H_MSG','WX_MIX_MSG','PUSH_LOG']}}
                ]
            },
            {'$set': {'lock':1}}, # 用于多线程互斥
            sort = [('_id',1)],
        )

    else: # 0 号会落到这里，只做杂事
        r = None

    if r:
        print tname, tid, 'event_quenu_id: ', str(r['_id']), str(r['type'])
        if r.get('count', 0)>10: # 防止“单据重复”进入死循环
            status = 'FAIL'
            msg = '多次重复'

        elif r['type']=='WX_MSG': # 微信推送通知
            status, msg = send_wx_msg(r)

        else:
            status = 'FAIL'
            msg = '未知事件'
        
        update_event_status(r['_id'], status, msg)
        time.sleep(0.5)

    else: # 无更新的，sleep
        # 闲时做点别的
        
        tt1 = int(time.time())
        
        refresh_session_timeout()

        # 清理推送事件
        # 测试时注释！！！
        r5=db.event_queue.delete_many({'type':'WX_MSG', 'status':{'$in' :['DONE','FAIL']}})

        tt2 = int(time.time())

        # sleep -------------
        idle_time = random.randint(2,DEALY) # 随机休息时长
        print tname,tid, 'sleep: ', idle_time, tt2-tt1, app_helper.time_str()
        time.sleep(idle_time)



class MainLoop(threading.Thread):
    def __init__(self, tid):
        threading.Thread.__init__(self)
        self._tid = tid
        self._tname = None

    def run(self):
        self._tname = threading.currentThread().getName()
        
        print 'Thread - started', self._tname, self._tid

        while 1:
            #main_loop(self._tname)
            try:
                check_event(self._tname, self._tid)
            except Exception, e:
                print 'Error: thread fail', self._tid, app_helper.time_str()
                traceback.print_exc()


            # 周期性打印日志
            sys.stdout.flush()

            time.sleep(0.1)


if __name__=='__main__':
    print "BACKRUN: %s started" % app_helper.time_str()

    gc.set_threshold(300,5,5)

    THREAD_NUM = 1 # 线程数量

    #线程池
    threads = []

    # 只为 strptime 不报异常
    # The first use of strptime is not thread safe because the first use will import _strptime. 
    time.strptime("2016-06-28 17:20:54","%Y-%m-%d %H:%M:%S")
    
    #清理上次遗留的 lock, 分布式部署时，启动时要小心，一定要在没有lock的情况下同时启动分布时进程！！！ 20150403
    db.event_queue.update_many({'lock':1}, {'$set': {'lock':0}})
    
    # 创建线程对象
    for x in xrange(0, THREAD_NUM):
        threads.append(MainLoop(x))
    
    print threads

    # 启动线程
    for t in threads:
        t.start()

    # 等待子线程结束
    for t in threads:
        t.join()  

    print "BACKRUN: %s exited" % app_helper.time_str()
