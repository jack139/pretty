#!/usr/bin/env python
# -*- coding: utf-8-*-
#


import web, json, copy
from bson.objectid import ObjectId
from config import setting
import app_helper
from libs import settings_helper
from libs import city_code
from libs import share_helper

db = setting.db_web

url = ('/app/v1/get_settings')

# 获取全局参数
class handler:
    def POST(self):
        web.header('Content-Type', 'application/json')

        param = web.input(app_id='', secret='', sign='', version='', next_day='')

        if '' in (param.app_id, param.secret, param.sign):
            return json.dumps({'ret' : -2, 'msg' : '参数错误'})

        # 验证签名
        md5_str = app_helper.generate_sign([param.app_id, param.secret, param.version, param.next_day])
        if md5_str!=param.sign:
            return json.dumps({'ret': -1, 'msg' : '签名验证错误'})

        # 更新app_id里的version
        db.app_device.update_one({'app_id':param.app_id},
                                 {'$set':{'version':param.version,
                                          'control_app_version': param.get('control_app_version','')}}
                                    )

        # 准备banner
        banner, banner_url = settings_helper.get_BANNER('app')
        # 填充新分类的banner, 与旧设置保持一致
        category3 = copy.deepcopy(app_helper.CATEGORY3)
        for i in category3:
            i['banner'] = banner['c001']
            i['banner_url'] = banner_url['c001']
        category4_2 = []
        category4 = copy.deepcopy(app_helper.CATEGORY4)
        for i in category4:
            if i['key']=='c000' and param.next_day.strip()!='1':
                continue
            i['banner'] = banner['c001']
            i['banner_url'] = banner_url['c001']
            category4_2.append(i)

        # 开机轮播
        db_bootimg = db.carousel_banner.find(
            {
                'expire_time' : {'$gt':app_helper.time_str(format=3)},
                'start_time'  : {'$lt':app_helper.time_str(format=3)},
            },
            sort=[('weight', 1)])
        bootimg = [[], [], [], [], [], []]
        bootimg_start = ''
        bootimg_expire = ''
        cccc = 0
        for xxx in db_bootimg:
            if len(xxx['images'])<6:
                continue
            bootimg[0].append('/%s/%s'%(xxx['images'][0][:2],xxx['images'][0]))
            bootimg[1].append('/%s/%s'%(xxx['images'][1][:2],xxx['images'][1]))
            bootimg[2].append('/%s/%s'%(xxx['images'][2][:2],xxx['images'][2]))
            bootimg[3].append('/%s/%s'%(xxx['images'][3][:2],xxx['images'][3]))
            bootimg[4].append('/%s/%s'%(xxx['images'][4][:2],xxx['images'][4]))
            bootimg[5].append('/%s/%s'%(xxx['images'][5][:2],xxx['images'][5]))

            bootimg_start = xxx['start_time']
            bootimg_expire = xxx['expire_time']

            cccc += 1
            if cccc==4: # 只放4个图片
                break

        print 'bootimg', bootimg

        # 首次启动图片
        db_cbanner = db.coupon_banner.find_one({'status':1})
        # app底部菜单分享文案（需分享的菜单） 20161028 lf
        menu_share = []
        app_button_menu = db.app_ui_style.find({'type': 'menu'})
        for u in app_button_menu:
            if int(u['share']) == 1:    # 可分享菜单才会有对应分享文案配置
                r = share_helper.share_paper('button_menu_'+u['menu_code'])
                menu_share.append({
                    'title': r['data']['title'] if r['ret'] == 0 else '',
                    'title2': r['data']['sub_title'] if r['ret'] == 0 else '',
                    'image': r['data']['image'] if r['ret'] == 0 else '',
                    'url': r['data']['url'] if r['ret'] == 0 else '',
                    'menu_code': u['menu_code']
                })
        # 区分版本号
        if int(param.get('control_app_version','250_old').split('_')[0]) >= 280:
            brand_url = '%s/static/wx/sourceAppNew/280/index.html#/brand/' % app_helper.H5_URL
            user_alert_url = '%s/static/wx/newreg/' % app_helper.H5_URL
            h5_poster_url = '%s/static/wx/ads/' % app_helper.H5_URL
            pt_detail_url = '%s/static/wx/sourceAppNew/280/index.html#/pt_detail/'% app_helper.H5_URL
        else:
            pt_detail_url = '/static/wx/sourceAppNew/280/index.html#/pt_detail/'
            brand_url = '/static/wx/sourceAppNew/280/index.html#/brand/'
            user_alert_url = '/static/wx/newreg/'
            h5_poster_url = '/static/wx/ads/'
        # 获取app ui的相关配置
        app_ui = db.app_ui_style.find_one({'type': 'home'})
        # 购物车推荐商品链接
        if app_helper.IS_TEST or app_helper.IS_STAGING:
            cart_promote_url = 'https://test-gateway.urfresh.cn'
        else:
            cart_promote_url = 'https://recommend.urfresh.cn'
        # 返回全局参数
        ret_data = {'ret' : 0, 'data' : {
            'delivery_fee'  : '%.2f' % app_helper.delivery_fee,
            'free_delivery' : '%.2f' % app_helper.free_delivery,
            'default_delivery_id': app_helper.default_delivery_id,
            'delivery_list': app_helper.new_delivery_list,
            'image_host2'   : 'http://%s/image/product' % setting.image_host,
            'image_host_https'   : setting.https_image_host,
            'notify_host'   : 'http://%s' % setting.notify_host,
            #'notify_host'   : 'http://app.urfresh.cn',
            'category3'     : category4_2,
            'pt_banner'     : settings_helper.get_app_pt_banner(),
            'if_pt_banner_show': True, # 应该与pt_banner联动
            'alert'         : app_helper.start_alert, # 多余
            'message'       : app_helper.start_message, # ios使用
            # 'message2'      : app_helper.start_message, # 安卓使用
            'hour_province' : ['上海'],
            'pt_category'   : app_helper.get_mall_category(),
            # 测试测试
            'boot_img_start' : bootimg_start,
            'boot_img_stop'  : bootimg_expire,
            'boot_img_list'  : bootimg,
            'service_tel'    : '400-966-9966',
            'versions_need_update_list'  : [], # ios
            'versions_under_update'      : '200',
            'versions_message_update'    : '亲，新功能上线啦，每日限时特价，类目五折，优惠多多！快来更新看看吧！',
            'can_enter_shop'  : 1,
            'first_install_img' : '/%s/%s'%(db_cbanner['image'][:2],db_cbanner['image']) if db_cbanner else '',
            'show_weekend_delivery' : app_helper.SHOW_WEEKEND_DELIVERY, # 是否显示周末送货选择
            'alipay_flag' : 1, # 是否显示支付宝推荐标签
            #'uploadFlumeServerUrl' : 'http://114.55.119.47/flume/',
            'uploadFlumeServerUrl' : 'http://gateway.urfresh.cn/flume/',
            'uploadFlumeServerUrl_https': 'https://test-gateway.urfresh.cn/flume/' if app_helper.IS_STAGING or app_helper.IS_TEST else 'https://gateway.urfresh.cn/flume/',
            'isUploadFlumeData' : 1,
            'page_size' : 100,
            'u_service_url': 'https://cdn.urfresh.cn/static/appweb/app/agreement.html',  # U掌柜服务协议H5链接
            'u_exchange_url': 'https://cdn.urfresh.cn/static/appweb/app/exchange.html',  # U掌柜关于售后退换货H5链接
            'u_ptrule_url': 'https://cdn.urfresh.cn/static/appweb/app/ptRules.html',  # U掌柜拼团活动规则
            'pt_detail_url': pt_detail_url,  # 拼团详情页面链接
            'brand_url': brand_url,  # 品牌团链接
            'user_alert_url': user_alert_url,  # 新用户注册链接
            'addr_flag'   : True,    #联想地址是否进行过滤
            'filter_city' : ['上海市'],      #联想地址需要过滤的城市
            'filter_info' : ['区县级地名', '乡镇级地名', '道路名'],      #联想地址过滤内容
            #'price_flag'  : app_helper.PRICE_FLAG, # 是否显示用券价
            'ntalker_enter_flag': True, # 控制客服入口显示
            'h5_poster_url'     : h5_poster_url,   #H5活动广告弹窗url
            'h5_poster_flag'    : False if int(app_ui.get('h5_poster',0)) == 0 else True, # H5活动广告弹窗的开关
            'top_bg_img'        : '/%s/%s' % (app_ui['icon'][10][:2], app_ui['icon'][10]) if len(app_ui['icon']) >= 11 else '',   #顶部栏背景图url
            'bottom_bg_img'     : '/%s/%s' % (app_ui['icon'][11][:2], app_ui['icon'][11]) if len(app_ui['icon']) >= 12 else '',  #底部栏背景图
            'top_bot_flag'      : True if int(app_ui['home_bg_img']) == 1 else False, #顶部和底部背景图开关
            'click_color':  app_ui['click_color'],    #底部菜单选中字体颜色
            'unclick_color': app_ui['unclick_color'],  #底部彩带未选中字体颜色
            'version_update_deleteImage' : '',
            'version_update_backImage'   : '',
            'force_update_backImage'     : '',
            'pt_page_size': 100,
            'control_app_version':param.get('control_app_version',''), # 微信用的
            'cart_promote_url': '%s/urfresh-recommend-api/v1/getRecommend' % cart_promote_url  # 购物车推荐商品服务器链接
        }}

        # 需要后台配的UI颜色
        ret_data['data']['color_dict'] = {
               'cate_title_color': app_ui['cate_title_color'],  #1小时/次日达,拼团页面头部类目字体颜色
               'pro_title_color': app_ui['pro_title_color'],  #商品标题颜色
               'pro_title2_color': app_ui['pro_title2_color'],   #商品副标题颜色
               'pro_rule_color': app_ui['pro_rule_color'],  #商品规则颜色
               'pro_price_color': app_ui['pro_price_color'],  #商品价格颜色
               'open_tuan_color': app_ui.get('open_tuan_color','8ebf30')  # 去开团图标颜色
        }
        # 需要后台配的UI icon图标
        ret_data['data']['icons_dict'] = {
            'first_add_cart': '%s/%s/%s' % (setting.https_image_host, app_ui['icon'][0][:2], app_ui['icon'][0]),    #首次加车的icon
            'sell_out_icon': '%s/%s/%s' % (setting.https_image_host, app_ui['icon'][1][:2], app_ui['icon'][1]),    #售罄的icon，如抢完了
            'highlight_add_cart': '%s/%s/%s' % (setting.https_image_host,app_ui['icon'][2][:2], app_ui['icon'][2]),  #高亮加车icon
            'highlight_reduce_cart':'%s/%s/%s' % (setting.https_image_host,app_ui['icon'][3][:2], app_ui['icon'][3]),  #高亮减车icon
            'gray_add_cart': '%s/%s/%s' % (setting.https_image_host,app_ui['icon'][4][:2], app_ui['icon'][4]),   #灰色加车icon
            'gray_reduce_cart': '%s/%s/%s' % (setting.https_image_host, app_ui['icon'][5][:2], app_ui['icon'][5]),  #灰色减车icon
            'select_cart_icon': '%s/%s/%s' % (setting.https_image_host, app_ui['icon'][6][:2], app_ui['icon'][6]),  #购物车选中icon
            'tab_cart_icon': '%s/%s/%s' % (setting.https_image_host, app_ui['icon'][7][:2], app_ui['icon'][7]),  #底部购物车菜单上显示的商品数量icon
            'to_tuan_icon': '%s/%s/%s' % (setting.https_image_host,app_ui['icon'][8][:2], app_ui['icon'][8])   #去开团icon
        }

        ret_data['data']['wxpay_enable17']=True  # 9月26日上架使用
        ret_data['data']['credit_enable17']=True
        ret_data['data']['menu_share_list']=menu_share

        ret_data['data']['wxpay_enable18']=True # 11月13日上架使用
        ret_data['data']['credit_enable18']=True

        ret_data['data']['wxpay_enable19']=True  # 11月28日上架使用
        ret_data['data']['credit_enable19']=True

        ret_data['data']['wxpay_enable20']=True  # 12月15日上架使用
        ret_data['data']['credit_enable20']=True

        ret_data['data']['wxpay_enable21']=True  # 1月13日上架使用
        ret_data['data']['credit_enable21']=True

        ret_data['data']['wxpay_enable22']=True  # 2月10日上架使用
        ret_data['data']['credit_enable22']=True

        ret_data['data']['wxpay_enable23']=False  # 3月10日上架使用
        ret_data['data']['credit_enable23']=False

        return json.dumps(ret_data)

