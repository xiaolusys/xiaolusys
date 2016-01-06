# coding: utf-8

from django.conf import settings

TARGET_SCHEMA = 'com.jimei.xlmm://'

# 跳转类型
TARGET_TYPE_HOME_TAB_1 = 1
TARGET_TYPE_HOME_TAB_2 = 2
TARGET_TYPE_HOME_TAB_3 = 3
TARGET_TYPE_HOME_TAB_4 = 4

# 聚合商品列表
TARGET_TYPE_MODELIST = 5
# 商品详情
TARGET_TYPE_PRODUCT = 6
# 订单详情
TARGET_TYPE_ORDER_DETAIL = 7
# 可用优惠券列表
TARGET_TYPE_AVAILABLE_COUPONS = 8
# Webview
TARGET_TYPE_WEBVIEW = 9

TARGET_PATHS = {
    TARGET_TYPE_HOME_TAB_1: 'app/v1/products/promote_today',
    TARGET_TYPE_HOME_TAB_2: 'app/v1/products/promote_previous',
    TARGET_TYPE_HOME_TAB_3: 'app/v1/products/childlist',
    TARGET_TYPE_HOME_TAB_4: 'app/v1/products/ladylist',
    TARGET_TYPE_MODELIST: 'app/v1/products/modelist',
    TARGET_TYPE_PRODUCT: 'app/v1/products',
    TARGET_TYPE_ORDER_DETAIL: 'app/v1/trades/details',
    TARGET_TYPE_AVAILABLE_COUPONS: 'app/v1/usercoupons/method',
    TARGET_TYPE_WEBVIEW: 'app/v1/webview'
}
