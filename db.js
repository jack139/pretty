
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

db.sku_store.createIndex({product_id:1})

db.wx_user.createIndex({wx_user:1})
db.wx_user.createIndex({last_tick:1},{ background: true })

db.event_queue.createIndex({lock:1,status:1,type:1},{ background: true })
db.event_queue.createIndex({type:1,status:1})
db.event_queue.createIndex({status:1})

db.coupons.createIndex({coupon_id:1,status:1})
db.coupons.createIndex({uname:1})
db.coupons.createIndex({openid:1})
db.coupons.createIndex({unionid:1})
db.coupons.createIndex({source_data:1},{ background: true })

db.unionid_index.createIndex({uname:1},{ background: true })
db.unionid_index.createIndex({openid:1},{ background: true })
db.unionid_index.createIndex({unionid:1},{ background: true })


db.sale_promote.createIndex({product_ids:1,status:1,type:1},{ background: true })
db.sale_promote.createIndex({promote_id:1},{ background: true })
db.sale_promote.createIndex({status:1},{ background: true })

db.coupons_active.createIndex({active_code:1,status:1},{ background: true })

db.coupons_set.createIndex({code:1,status:1},{ background: true })

db.code_province.createIndex({id:1},{ background: true })
db.code_province.createIndex({status:1},{ background: true })

db.code_city.createIndex({id:1},{ background: true })
db.code_city.createIndex({province_id:1},{ background: true })
db.code_city.createIndex({status:1,province_id:1},{ background: true })

db.code_county.createIndex({id:1},{ background: true })
db.code_county.createIndex({city_id:1},{ background: true })
db.code_county.createIndex({status:1,city_id:1},{ background: true })




