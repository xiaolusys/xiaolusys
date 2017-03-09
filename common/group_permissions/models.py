# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class GroupPermissions(models.Model): #自定义权限绑定表
    sale_category = models.CharField(max_length=32, blank=True, verbose_name=u'自定义权限')

    class Meta:
        db_table = 'customize_permissions'
        app_label = 'group_permissions'
        verbose_name = u'自定义权限'
        verbose_name_plural = u'自定义权限表'
        permissions = (
            ("manage_sale_supplier", u"醉了"),
            # ("manage_sale_supplier", u"管理供应商"),
            # ('manage_sale_category', u'管理特卖/选品列表'),
            # ('add_product', u'管理排期'),
            # ('manage_sale_manage_detail', u'管理排期明细'),
            # ('manage_preference_pool', u'管理特卖/产品资料参数表'),
            # ('manage_xiaolumama', u'管理小鹿妈妈'),
            # ('manage_apppushmsg', u'管理消息推送'),
            # ('manage_user_budget', u'管理特卖/APP全站推送'),
            # ('manage_user_coupon', u'管理特卖/优惠券/用户优惠券表'),
            # ('manage_transfer_coupondetail', u'管理特卖/优惠券/流通明细表'),
            # ('manage_ninepicadver', u'设置9张图'),
            # ('manage_change_uppermama', u'更改上级妈妈'),
            # ('manage_mall_activity', u'管理商城活动'),
        )