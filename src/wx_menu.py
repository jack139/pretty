#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2, urllib
import json
#from config import setting

# 东南
wx_appid='wxbbf4e9f80fd0dd60'
wx_secret='a21841796b00eeb515695ceb64ad202b'

wx_menu={
    'button':[
        {
            'type' : 'view',
            'name' : '超市',
            'url'  : 'http://wxdn.urfresh.cn/wx/init_herb',
        },
        {
            'name':'我的',
            'sub_button':[
                {
                    'type' :'view',
                    'name' :'我的订单',
                    'url'  : 'http://.../wx/init_my_order',
                },
                {
                    'type' :'view',
                    'name' :'个人中心',
                    'url'  : 'http://.../wx/init_user_info',
                },
                {
                    'type':'click',
                    'name':'在线客服',
                    'key'  : 'CLICK_SERVICE',
                },
            ]
        },
    ]
}

def get_token():
	url='https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=%s&secret=%s' % \
		(wx_appid, wx_secret)
	f=urllib.urlopen(url)
	data = f.read()
	f.close()

	t=json.loads(data)
	if t.has_key('access_token'):
		return t['access_token']
	else:
		return ''

def creat_menu(access_token):
	t=json.dumps(wx_menu, ensure_ascii=False)
	f = urllib2.urlopen(
		url	= 'https://api.weixin.qq.com/cgi-bin/menu/create?access_token=%s' % access_token,
		data	= t
		)
	ret=f.read()
	print ret

if __name__ == '__main__':
	my_token=get_token()
	#my_token='cI4OABcORaGjqdXhQmfGLbPv0CHgSxQpQmUsAJeNyLhe8Fy5i_L6NcB6bTze59QXvbXoMcKQXsV9Lo6TLCScYA'
	print my_token

	creat_menu(my_token)

