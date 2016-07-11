# -*- coding:utf-8 -*-
import random, string
import datetime
from django.db import models

from core.models import BaseModel
from .freesample import XLSampleApply, XLSampleOrder

from ..managers import VipCodeManager

SAFE_CODE_SECONDS = 180
TOKEN_EXPIRED_IN = 15 * 60


class XLInviteCode(BaseModel):
    """ 用户活动邀请码 """
    CODE_TYPES = ((0, u'免费试用'), (1, u'招募代理'))

    mobile = models.CharField(max_length=11, unique=True, verbose_name=u'手机号码')

    vipcode = models.CharField(max_length=16, unique=True, null=False,
                               blank=False, verbose_name=u'邀请码')
    expiried = models.DateTimeField(null=False, blank=False, verbose_name=u'过期时间')

    ### 1. for getting samples; 2. for purchase discount
    code_type = models.IntegerField(default=0, choices=CODE_TYPES, verbose_name=u'邀请码类型')

    ### get $10 for $50 purchase; get $25 for $100 purchase;
    code_rule = models.CharField(max_length=256, null=False, blank=True, verbose_name=u'使用规则')

    ### once or multiple times
    max_usage = models.IntegerField(default=0, verbose_name=u'可用次数')
    usage_count = models.IntegerField(default=0, db_index=True, verbose_name=u'已使用')

    objects = VipCodeManager()

    class Meta:
        db_table = 'flashsale_promotion_invitecode'
        app_label = 'promotion'
        verbose_name = u'推广/活动邀请码'
        verbose_name_plural = u'推广/活动邀请码列表'


class XLInviteCount(BaseModel):
    customer = models.OneToOneField('pay.Customer', verbose_name=u'特卖用户')
    apply_count = models.IntegerField(default=0, verbose_name=u'申请人数')
    invite_count = models.IntegerField(default=0, verbose_name=u'激活人数')
    click_count = models.IntegerField(default=0, verbose_name=u'点击次数')

    class Meta:
        db_table = 'flashsale_promotion_invitecount'
        app_label = 'promotion'
        verbose_name = u'推广/活动邀请结果'
        verbose_name_plural = u'推广/活动邀请结果列表'


class XLReferalRelationship(BaseModel):
    """ 用户邀请引用关系 """

    referal_uid = models.CharField(max_length=64, unique=True, verbose_name=u"被推荐人ID")
    referal_from_uid = models.CharField(max_length=64, db_index=True, verbose_name=u"推荐人ID")

    class Meta:
        db_table = 'flashsale_promotion_relationship'
        app_label = 'promotion'
        verbose_name = u'推广/用户邀请关系'
        verbose_name_plural = u'推广/用户邀请关系'


from django.db.models.signals import post_save


def sampleorder_create_and_update_count(sender, instance, created, *args, **kwargs):
    """ 试用订单更新邀请数 """
    if not created:
        return
    xlapply = XLSampleApply.objects.get(id=instance.xlsp_apply)
    inv_count, state = XLInviteCount.objects.get_or_create(customer_id=xlapply.from_customer)
    inv_count.invite_count = models.F('invite_count') + 1
    inv_count.save()


post_save.connect(sampleorder_create_and_update_count, sender=XLSampleOrder)

from django.db.models.signals import post_save


def sampleapply_create_and_update_count(sender, instance, created, *args, **kwargs):
    """ 试用订单更新邀请数 """
    if not created or not instance.from_customer:
        return
    inv_count, state = XLInviteCount.objects.get_or_create(customer_id=instance.from_customer)
    inv_count.apply_count = models.F('apply_count') + 1
    inv_count.save()


post_save.connect(sampleapply_create_and_update_count, sender=XLSampleApply)
