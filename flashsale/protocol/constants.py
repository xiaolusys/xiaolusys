# coding: utf-8
from django.conf import settings

TARGET_SCHEMA = 'com.jimei.xlmm://'

# 跳转类型
TARGET_TYPE_HOME_TAB_1 = 1
TARGET_TYPE_HOME_TAB_2 = 2
TARGET_TYPE_HOME_TAB_3 = 3
TARGET_TYPE_HOME_TAB_4 = 4

TARGET_TYPE_MODELIST = 5  # 聚合商品列表
# TARGET_TYPE_PRODUCT = 6 弃用 # 商品详情
TARGET_TYPE_ORDER_DETAIL = 7  # 订单详情
TARGET_TYPE_AVAILABLE_COUPONS = 8  # 可用优惠券列表
TARGET_TYPE_WEBVIEW = 9  # Webview
TARGET_TYPE_VIP_HOME = 10  # 小鹿妈妈
TARGET_TYPE_VIP_0DAY = 11  # 小鹿妈妈每日上新
TARGET_TYPE_REFUNDS = 12  # 退款退货列表
TARGET_TYPE_AT = 13  # 论坛at人推送返回论坛首页
TARGET_TYPE_SHOPPING_CART = 14  # 购物车
TARGET_TYPE_ACTIVE = 15  # 活动
TARGET_TYPE_CATEGORY_PRO = 16  # 分类商品

TARGET_PATHS = {
    TARGET_TYPE_HOME_TAB_1: 'app/v1/products/promote_today',
    TARGET_TYPE_HOME_TAB_2: 'app/v1/products/promote_previous',
    TARGET_TYPE_HOME_TAB_3: 'app/v1/products/childlist',
    TARGET_TYPE_HOME_TAB_4: 'app/v1/products/ladylist',

    TARGET_TYPE_MODELIST: 'app/v1/products/modelist',
    TARGET_TYPE_ORDER_DETAIL: 'app/v1/trades/details',
    TARGET_TYPE_AVAILABLE_COUPONS: 'app/v1/usercoupons/method',
    TARGET_TYPE_WEBVIEW: 'app/v1/webview',
    TARGET_TYPE_VIP_HOME: 'app/v1/vip_home',
    TARGET_TYPE_VIP_0DAY: 'app/v1/vip_0day',
    TARGET_TYPE_REFUNDS: 'app/v1/refunds',
    TARGET_TYPE_AT: 'app/v1/vip_forum',
    TARGET_TYPE_SHOPPING_CART: 'app/v1/shopping_cart',
    TARGET_TYPE_ACTIVE: 'app/v1/webview',
    TARGET_TYPE_CATEGORY_PRO: 'app/v1/products/category'
}
