# coding:utf-8
from django.db import models

from core.models import BaseModel
from core.fields import JSONCharMyField

from . import constants


class APPFullPushMessge(BaseModel):
    """ APP消息全推 
    result:{
        "code":0,
        "result":"ok",
        "description":"成功",
        "data":{"id":"1000999_1375164696370"},
        "info":"Received push messages for 1 regid"
    }
    """
    FAIL = 0
    SUCCESS = 1
    STATUSES = (
        (FAIL, u'失败'),
        (SUCCESS, u'生效')
    )

    PL_IOS = 'ios'
    PL_ANDROID = 'android'
    PLATFORM_CHOICES = (
        (PL_IOS, '全部IOS用户'),
        (PL_ANDROID, '全部ANDROID用户')
    )

    TARGET_CHOICES = (
        (constants.TARGET_TYPE_HOME_TAB_1, '今日上新'),
        (constants.TARGET_TYPE_HOME_TAB_2, '昨日特卖'),
        (constants.TARGET_TYPE_HOME_TAB_3, '潮童专区'),
        (constants.TARGET_TYPE_HOME_TAB_4, '时尚女装'),
        (constants.TARGET_TYPE_MODELIST, '商品款式页'),
        (constants.TARGET_TYPE_PRODUCT, '商品详情页'),
        (constants.TARGET_TYPE_ORDER_DETAIL, '订单详情页'),
        (constants.TARGET_TYPE_AVAILABLE_COUPONS, '优惠券列表'),
        (constants.TARGET_TYPE_WEBVIEW, 'APP活动页'),
        (constants.TARGET_TYPE_VIP_HOME, '小鹿妈妈首页'),
    )

    class Meta:
        app_label = 'apprelease'
        db_table = 'flashsale_apppushmsg'
        verbose_name = u'特卖/APP全站推送'
        verbose_name_plural = u'特卖/APP全站推送'

    desc = models.TextField(max_length=256, verbose_name=u'推送内容(限200字)')
    target_url = models.IntegerField(default=constants.TARGET_TYPE_HOME_TAB_1,
                                     choices=TARGET_CHOICES, verbose_name='跳转页面')
    params = JSONCharMyField(max_length=512, default=lambda: {}, blank=True, verbose_name=u'推送参数')
    cat = models.PositiveIntegerField(blank=True, default=0, verbose_name=u'分类')
    platform = models.CharField(db_index=True, choices=PLATFORM_CHOICES, max_length=16, verbose_name=u'平台')
    regid = models.CharField(max_length=512, blank=True, verbose_name=u'小米regid')
    result = JSONCharMyField(max_length=2048, default=lambda: {}, blank=True, verbose_name=u'推送结果')
    status = models.SmallIntegerField(db_index=True, choices=STATUSES, default=FAIL, verbose_name=u'状态')
