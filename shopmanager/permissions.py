# coding=utf-8
"""
    自定义的权限尽量在此记录
"""

from django.contrib.auth.models import Permission,Group
from django.contrib.contenttypes.models import ContentType


permission_trades = [
    # ('manage_package_order', ('trades', 'packageorder'), 'manage package order', u'管理供应商')
    ('manage_sale_supplier', ('supplier', 'salesupplier'), 'manage sale supplier', u'管理供应商'),
    ('manage_sale_category', ('supplier', 'salecategory'), 'manage sale category', u'管理特卖/选品类目'),
    ('manage_sale_product', ('supplier', 'saleproduct'), 'manage sale product', u'管理特卖/选品列表'),
    ('manage_sale_manage', ('supplier', 'saleproductmanage'), 'manage sale manage', u'管理排期'),
    ('manage_sale_manage_detail', ('supplier', 'saleproductmanagedetail'), 'manage sale manage detail', u'管理排期明细'),
    ('manage_preference_pool', ('supplier', 'preferencepool'), 'manage preference pool', u'管理特卖/产品资料参数表'),
    ('manage_xiaolumama', ('xiaolumm', 'xiaolumama'), 'manage xiaolumama', u'更换/设置/妈妈的上级妈妈'),
    ('manage_apppushmsg', ('protocol', 'appfullpushmessge'), 'manage apppushmsg', u'管理消息推送'),
    ('manage_user_budget', ('pay', 'userbudget'), 'manage user budget', u'发送红包: 创建用户budget_log记录'),
    ('manage_user_coupon', ('coupon', 'usercoupon'), 'manage user coupon', u'管理特卖/优惠券/用户优惠券表'),
    ('manage_transfer_coupondetail', ('coupon', 'transfercoupondetail'), 'manage transfer coupondetail', u'特卖/精品券流通记录'),
    ('manage_ninepicadver', ('xiaolumm', 'ninepicadver'), 'manage ninepicadver', u'设置9张图'),
    ('manage_mall_activity', ('pay', 'activityentry'), 'manage mall activity', u'管理商城活动')
]

permissions = []
permissions.extend(permission_trades)


def update_permissions():
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    for permission in permissions:
        content_type = ContentType.objects.get(app_label=permission[1][0], model=permission[1][1])
        Permission.objects.get_or_create(name=permission[2], content_type=content_type, codename=permission[0])
# 获取权限对应的model
# from django.apps import apps
# apps.get_models('trades', 'packageorder')

def update_salesupplier_permissions():  #管理供应商
    content_type = ContentType.objects.get(app_label="supplier", model="salesupplier")
    Permission.objects.get_or_create(name="manage sale supplier", content_type=content_type, codename="manage_sale_supplier")
    perm = Permission.objects.get(name="manage sale supplier",codename="manage_sale_supplier")
    g=Group.objects.get(id=18)
    g.permissions.add(perm.id)

def update_salecategory_permissions():  #管理特卖/选品类目
    content_type = ContentType.objects.get(app_label="supplier", model="salecategory")
    Permission.objects.get_or_create(name="manage sale category", content_type=content_type, codename="manage_sale_category")

def update_saleproduct_permissions():   #管理特卖/选品列表
    content_type = ContentType.objects.get(app_label="supplier", model="saleproduct")
    Permission.objects.get_or_create(name="manage sale product", content_type=content_type, codename="manage_sale_product")

def update_salemanage_permissions():    #管理排期
    content_type = ContentType.objects.get(app_label="supplier", model="saleproductmanage")
    Permission.objects.get_or_create(name="manage sale manage", content_type=content_type, codename="manage_sale_manage")


def update_salemanagedetail_permissions():  #管理排期明细
    content_type = ContentType.objects.get(app_label="supplier", model="saleproductmanagedetail")
    Permission.objects.get_or_create(name="manage sale manage detail", content_type=content_type, codename="manage_sale_manage_detail")


def update_preferencepool_permissions():    #管理特卖/产品资料参数表
    content_type = ContentType.objects.get(app_label="supplier", model="preferencepool")
    Permission.objects.get_or_create(name="manage preference pool", content_type=content_type, codename="manage_preference_pool")


def update_xiaolumama_permissions():    #更换/设置/妈妈的上级妈妈
    content_type = ContentType.objects.get(app_label="xiaolumm", model="xiaolumama")
    Permission.objects.get_or_create(name="manage xiaolumama", content_type=content_type, codename="manage_xiaolumama")


def update_appfullpush_permissions():   #管理消息推送
    content_type = ContentType.objects.get(app_label="protocol", model="appfullpushmessge")
    Permission.objects.get_or_create(name="manage apppushmsg", content_type=content_type, codename="manage_apppushmsg")


def update_sendbudgetenvelop_permissions():    #发送红包: 创建用户budget_log记录
    content_type = ContentType.objects.get(app_label="pay", model="userbudget")
    Permission.objects.get_or_create(name="manage user budget", content_type=content_type, codename="manage_user_budget")


def update_usercoupon_permissions():        #管理特卖/优惠券/用户优惠券表
    content_type = ContentType.objects.get(app_label="coupon", model="usercoupon")
    Permission.objects.get_or_create(name="manage user coupon", content_type=content_type,codename="manage_user_coupon")

def update_coupontransferrecord_permissions():  #特卖/精品券流通记录
    content_type = ContentType.objects.get(app_label="coupon", model="transfercoupondetail")
    Permission.objects.get_or_create(name="manage transfer coupondetail", content_type=content_type,codename="manage_transfer_coupondetail")

def update_ninepicadver_permissions():    #设置9张图
    content_type = ContentType.objects.get(app_label="xiaolumm", model="ninepicadver")
    Permission.objects.get_or_create(name="manage ninepicadver", content_type=content_type,codename="manage_ninepicadver")

def update_mallactivity_permissions():    #管理商城活动
    content_type = ContentType.objects.get(app_label="pay", model="activityentry")
    Permission.objects.get_or_create(name="manage mall activity", content_type=content_type,codename="manage_mall_activity")

    




