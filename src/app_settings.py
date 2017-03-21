#
# 以下配置文件均为实际代码，对格式有严格要求，请遵守：
# 1. 行首缩紧必须用tab, 不能使用空格，尤其不能空格与tab混用
# 2. 英文井号 # 开头为注释，可随便写
# 3. 连续3个单引号 ''' ... ''' 标示整段的注释，起始位置要纵向对齐
#

##############################################



# app使用的新分类
CATEGORY = [
    {
        'key': 'c001', 'title': '分类',
        'banner': (
            'http://wx.acmecareonline.com/static/image/banner/20170207_1.png',
            'http://wx.acmecareonline.com/static/image/banner/20170110_1.png',
            'http://wx.acmecareonline.com/static/image/banner/20170110_2.png',
            'http://wx.acmecareonline.com/static/image/banner/20170110_3.png',
            'http://wx.acmecareonline.com/static/image/banner/20161224_1.png',
            'http://wx.acmecareonline.com/static/image/banner/20161224_2.png',
        ),
        'banner_url': ('10000010','10000009','10000007','10000008','10000004','10000005')
    },
]



# 默认免邮门槛、运费
free_delivery = 200  # 免邮门槛
delivery_fee = 10  # 邮费


# ------  不首单立减，注册后发券
# 默认首单立减设置
first_promote = 0    # 首单立减
first_promote_threshold = 10000    # 首单立减


# 默认推荐标签(首页、详情页)，不需要修改
defaut_promote_img = '/promote.png'



# 抵用券活动设置
COUPON_SET = {
    'ORDER_1H_NEW': '160530qum', # 下单红包1小时新客
    'ORDER_1H_OLD': '160515ope', # 下单红包1小时老客
    'ORDER_PT_NEW': '160515ucm', # 下单红包拼团新客
    'ORDER_PT_OLD': '160515sax', # 下单红包拼团老客
    'INVIT'       : '160515bgm', #邀请码
    'INVIT2016'   : '160515pln', #邀请码2016
    'INVIT_ORDER' : '160515uob', #邀请码好友下单
    'NEW_REG'     : '160515ddn', #新用户注册
}

# 确认收货发券
CONFIRM_GIVE_COUPN = 1

# 收货确认发券图标
CONFIRM_FLAG = '160523sqw'


# 订单备注标签
NOTE_LABEL = [
    '西瓜切片',
    '蜜瓜切片',
    '椰青打开',
    '菠萝/凤梨切片',
    '榴莲剥肉',
]
