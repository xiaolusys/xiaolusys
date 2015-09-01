# coding= utf-8
"""
模板：负责优惠券的定义（用途，价值，标题）
券池：负责不同优惠券的生成，查询，发放，作废
用户：负责记录用户优惠券持有状态
"""
from django.db import models
import datetime
from options import uniqid


class CouponTemplate(models.Model):
    RMB118 = 0
    POST_FEE = 1
    COUPON_TYPE = ((RMB118, u"二期代理优惠券"), (POST_FEE, u"退货补邮费"))

    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")
    value = models.FloatField(default=1.0, verbose_name=u"优惠券价值")
    valid = models.BooleanField(default=False, verbose_name=u"是否有效")
    type = models.IntegerField(choices=COUPON_TYPE, verbose_name=u"优惠券类型")
    preset_days = models.IntegerField(default=0, verbose_name=u"预置天数")
    active_days = models.IntegerField(default=0, verbose_name=u"有效天数")
    deadline = models.DateTimeField(blank=True, verbose_name=u'截止日期')
    use_notice = models.TextField(blank=True, verbose_name=u"使用须知")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = "pay_coupon_template"
        verbose_name = u"特卖/优惠券/模板/NEW"
        verbose_name_plural = u"优惠券/模板/NEW"

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.title)


class CouponsPool(models.Model):
    RELEASE = 1
    UNRELEASE = 0
    PAST = 2
    POOL_COUPON_STATUS = ((RELEASE, u"已发放"), (UNRELEASE, u"未发放"), (PAST, u"已过期"))

    template = models.ForeignKey(CouponTemplate, verbose_name=u"模板ID")
    coupon_no = models.CharField(max_length=32, db_index=True, unique=True, default=lambda: uniqid(
        '%s%s' % ('YH', datetime.datetime.now().strftime('%y%m%d'))), verbose_name=u"优惠券号码")
    status = models.IntegerField(default=UNRELEASE, choices=POOL_COUPON_STATUS, verbose_name=u"发放状态")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        db_table = "pay_coupon_pool"
        verbose_name = u"特卖/优惠券/券池/NEW"
        verbose_name_plural = u"优惠券/券池/NEW"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.template.title)


class UserCoupon(models.Model):
    USED = 1
    UNUSED = 0
    USER_COUPON_STATUS = ((USED, u"已使用"), (UNUSED, u"未使用"))

    cp_id = models.ForeignKey(CouponsPool, db_index=True, verbose_name=u"优惠券ID")
    customer = models.CharField(max_length=32, db_index=True, verbose_name=u"顾客ID")
    sale_trade = models.CharField(max_length=32, db_index=True, verbose_name=u"绑定交易ID")
    status = models.IntegerField(default=UNUSED, choices=USER_COUPON_STATUS, verbose_name=u"使用状态")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(auto_now=True, verbose_name=u'修改日期')

    class Meta:
        unique_together = ('cp_id', 'customer')
        db_table = "pay_user_coupon"
        verbose_name = u"特卖/优惠券/用户优惠券/NEW"
        verbose_name_plural = u"优惠券/用户优惠券/NEW"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.customer)

