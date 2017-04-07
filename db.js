﻿user  后台用户表：系统用户(admin)、平谷用户、商家用户
merchant    商家企业
    mch_id  商家id
    name    名称
    type    类型： self 自营  mcht 入驻商家   
    available   是否有效

obj_store      商品：试听课程、精品课程
    obj_id  商品id
    media    媒体类型： audio 音频 video 视频
    obj_name    对象名称，内部使用
    title   标题
    title2  副标题
    speaker 讲师
    image   标题图片
    length  长度，单位：秒
    try_time    试听时长，单位秒，0表示不能试听
    cate_id 分类id
    price   价格
    volume  销量
    file_path   下载文件地址
    tpc_id  所属专辑id
    available   是否有效
    list_in_app 是否上架
    start_time  上架开始时间
    stop_time   上架结束时间

topic_store      专辑
    tpc_id  专辑id
    type    类型： audio 音频 video 视频
    title   标题
    title2  副标题
    image   标题图片
    length  长度，几堂课
    available   是否有效

order_trade   支付交易订单
    order_trade_id   交易流水号
    userid      用户id
    alipay_trade_no 支付宝流水号
    wxpay_trade_no  微信支付流水号
    total_sum   发生总金额，单位：分
    cash_sum    余额发生金额
    alipay_sum  支付宝发生金额
    wxpay_sum   微信支付发生金额
    type    交易类型： receipt 收款   refund 退款
    pay_type    cash 余额 alipay 支付宝 wxpay 微信支付
    pay_time    付款时间

order_app   购买订单
    order_id    订单号 
    userid      用户id
    cart        购物车信息
    status  订单状态
    type    订单类型： virtual 虚拟商品  entity  实物商品
    order_time    下单时间
    order_trade_id   交易订单号

order_recharge  充值订单
    recharge_id     充值流水号
    order_trade_id   交易订单号
    recharge_sum    充值金额，单位 分
    pay_sum     付款金额，单位 分

app_user    线上用户
    userid      用户id
    uname       电话号码／openid
    unionid     微信使用unionid
    nickname    微信昵称
    img_url     微信头像

cash_info   用户充值帐户
    userid      用户id
    balance     余额金额, 单位 分


auth_info   授权信息
    userid      用户id
    obj_list    被授权的对象id

heart_info  收藏信息
    userid  用户id
    obj_list    收藏的对象id

progress_info   学习进度
    userid  用户id
    obj_id  对象id
    progress    进度，百分比

comment_info    评价信息
    userid  用户id
    obj_id  对象id
    star    星级
    comment 评价内容

exam_info   课程测试

test_info   测试答案信息

banner_info 轮播图设置
    banner_id   轮播图id
    category    分类
    start_time  开始时间
    stop_time   结束时间
    image_path  图片url
    click_url   点击跳转的url

category_info 分类信息
    cate_id     分类id
    title       分类名
    start_time  开始时间
    stop_time   结束时间
    

用户注册／登录过程：
1. 手机号码注册／登录：短信验证码
2. 微信登录：
    openid是否存在？
        是：是否已绑定？
            是：登录成功
            否：绑定手机号：手机号是否存在？
                是：绑定手机，使用同一userid
                否：自动注册手机用户，使用同一userid
        否：创建微信用户，userid为空，返回需绑定手机


/* -------------- Indexes ---------------*/

/* 后台建索引 db.collection.createIndex( { a: 1 }, { background: true } ) */

db.user.createIndex({privilege:1})
db.user.createIndex({uname:1})
db.user.createIndex({login:1, privilege:1})

db.sessions.createIndex({session_id:1})

db.app_device.createIndex({app_id:1})

db.app_sessions.createIndex({session_id:1})
db.app_sessions.createIndex({attime:1})
db.app_sessions.createIndex({type:1,attime:1})
db.app_sessions.createIndex({login:1,attime:1})
db.app_sessions.createIndex({uname:1})

db.app_user.createIndex({uname:1})
db.app_user.createIndex({app_id:1})
db.app_user.createIndex({openid:1})
db.app_user.createIndex({last_status:1},{ background: true })
db.app_user.createIndex({reg_time:1})

db.order_app.createIndex({order_id:1, user:1})
db.order_app.createIndex({b_time:1},{background:true})
db.order_app.createIndex({last_status:1},{background:true})
db.order_app.createIndex({user:1, status:1, order_id:1})
db.order_app.createIndex({uname:1, order_id:1})
db.order_app.createIndex({uname:1, status:1, deadline:1})
db.order_app.createIndex({status:1, deadline:1})
db.order_app.createIndex({order_id:1})
db.order_app.createIndex({status:1, type:1, 'address.8':1})
db.order_app.createIndex({'address.2':1})
db.order_app.createIndex({wx_out_trade_no:1})
db.order_app.createIndex({ali_trade_no:1})
db.order_app.createIndex({crm_time:1},{background:true})

db.base_image.createIndex({image:1})


db.wx_user.createIndex({wx_user:1})
db.wx_user.createIndex({last_tick:1},{ background: true })


db.coupons.createIndex({coupon_id:1,status:1})
db.coupons.createIndex({uname:1})
db.coupons.createIndex({openid:1})
db.coupons.createIndex({unionid:1})
db.coupons.createIndex({source_data:1},{ background: true })

db.unionid_index.createIndex({uname:1},{ background: true })
db.unionid_index.createIndex({openid:1},{ background: true })
db.unionid_index.createIndex({unionid:1},{ background: true })


db.code_province.createIndex({id:1},{ background: true })
db.code_province.createIndex({status:1},{ background: true })

db.code_city.createIndex({id:1},{ background: true })
db.code_city.createIndex({province_id:1},{ background: true })
db.code_city.createIndex({status:1,province_id:1},{ background: true })

db.code_county.createIndex({id:1},{ background: true })
db.code_county.createIndex({city_id:1},{ background: true })
db.code_county.createIndex({status:1,city_id:1},{ background: true })




