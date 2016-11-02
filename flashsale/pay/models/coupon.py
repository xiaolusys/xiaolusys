# coding= utf-8
"""
模板：负责优惠券的定义（用途，价值，标题）
券池：负责不同优惠券的生成，查询，发放，作废
用户：负责记录用户优惠券持有状态
"""
from django.db import models
import datetime

from core.models import BaseModel
from ..options import uniqid
from .user import Customer


class CouponTemplate(BaseModel):
    RMB118 = 0
    POST_FEE_5 = 1
    POST_FEE_10 = 4
    POST_FEE_15 = 5
    POST_FEE_20 = 7
    C150_10 = 2
    C259_20 = 3
    DOUBLE_11 = 6
    DOUBLE_12 = 8
    USUAL = 9
    NEW_YEAR = 10
    PROMMOTION_TYPE = 11
    COUPON_TYPE = ((RMB118, u"代理优惠券"), (POST_FEE_5, u"5元退货补邮费"),
                   (POST_FEE_10, u"10元退货补邮费"), (POST_FEE_15, u"15元退货补邮费"), (POST_FEE_20, u"20元退货补邮费"),
                   (C150_10, u"满150减10"), (C259_20, u"满259减20"), (DOUBLE_11, u"双11专用"), (DOUBLE_12, u"双12专用"),
                   (USUAL, u"普通"), (NEW_YEAR, u"元旦专用"), (PROMMOTION_TYPE, u"活动类型"))
    CLICK_WAY = 0
    BUY_WAY = 1
    XMM_LINK = 2
    PROMOTION = 3
    COUPON_WAY = ((CLICK_WAY, u"点击方式领取"), (BUY_WAY, u"购买商品获取"), (XMM_LINK, u"购买专属链接"),
                  (PROMOTION, u"活动发放"))
    ALL_USER = 1
    AGENCY_VIP = 2
    AGENCY_A = 3
    TAR_USER = ((ALL_USER, u"所有用户"), (AGENCY_A, u"A类代理"), (AGENCY_VIP, u"VIP代理"))

    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")
    value = models.FloatField(default=1.0, verbose_name=u"优惠券价值")
    valid = models.BooleanField(default=False, verbose_name=u"是否有效")
    type = models.IntegerField(choices=COUPON_TYPE, verbose_name=u"优惠券类型")
    nums = models.IntegerField(default=0, verbose_name=u"发放数量")
    limit_num = models.IntegerField(default=1, verbose_name=u"每人领取数量")

    use_fee = models.FloatField(default=0.0, verbose_name=u'满多少元可以使用')  # 满多少可以使用
    release_fee = models.FloatField(default=0.0, verbose_name=u'满多少元可以发放')  # 满多少可以发放

    bind_pros = models.CharField(max_length=256, null=True, blank=True, verbose_name=u'绑定可以使用的产品')  # 指定产品可用

    use_pro_category = models.CharField(max_length=256, blank=True, verbose_name=u'可以使用产品的类别')

    release_start_time = models.DateTimeField(blank=True, verbose_name=u'开始发放的时间')
    release_end_time = models.DateTimeField(blank=True, verbose_name=u'结束发放的时间')

    start_use_time = models.DateTimeField(blank=True, verbose_name=u'开始使用的时间')

    deadline = models.DateTimeField(blank=True, verbose_name=u'截止使用的时间')

    use_notice = models.TextField(blank=True, verbose_name=u"使用须知")
    way_type = models.IntegerField(default=0, choices=COUPON_WAY, verbose_name=u"领取途径")
    target_user = models.IntegerField(default=0, choices=TAR_USER, verbose_name=u"目标用户")
    post_img = models.CharField(max_length=512, blank=True, null=True, verbose_name=u"模板图片")

    class Meta:
        db_table = "pay_coupon_template"
        app_label = 'pay'
        verbose_name = u"特卖/优惠券/模板/NEW"
        verbose_name_plural = u"优惠券/模板/NEW"

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.title)


def default_coupon_no():
    return uniqid('%s%s' % ('YH', datetime.datetime.now().strftime('%y%m%d')))

class CouponsPool(BaseModel):
    RELEASE = 1
    UNRELEASE = 0
    PAST = 2
    POOL_COUPON_STATUS = ((RELEASE, u"已发放"), (UNRELEASE, u"未发放"), (PAST, u"已过期"))

    template = models.ForeignKey(CouponTemplate, verbose_name=u"模板ID", null=True, on_delete=models.SET_NULL)
    coupon_no = models.CharField(max_length=32, db_index=True, unique=True,
                                 default=default_coupon_no,
                                 verbose_name=u"优惠券号码")
    status = models.IntegerField(default=UNRELEASE, choices=POOL_COUPON_STATUS, verbose_name=u"发放状态")

    class Meta:
        db_table = "pay_coupon_pool"
        app_label = 'pay'
        verbose_name = u"特卖/优惠券/券池/NEW"
        verbose_name_plural = u"优惠券/券池/NEW"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.template)


class UserCoupon(BaseModel):
    USED = 1
    UNUSED = 0
    FREEZE = 2
    USER_COUPON_STATUS = ((USED, u"已使用"), (UNUSED, u"未使用"), (FREEZE, u"冻结中"))
    """冻结中，领取后多少天后可以使用，即暂时冻结中"""

    cp_id = models.ForeignKey(CouponsPool, db_index=True, verbose_name=u"优惠券ID")
    customer = models.CharField(max_length=32, db_index=True, verbose_name=u"顾客ID")
    sale_trade = models.CharField(max_length=32, db_index=True, verbose_name=u"绑定交易ID")
    status = models.IntegerField(default=UNUSED, choices=USER_COUPON_STATUS, verbose_name=u"使用状态")

    class Meta:
        unique_together = ('cp_id', 'customer')
        db_table = "pay_user_coupon"
        app_label = 'pay'
        verbose_name = u"特卖/优惠券/用户优惠券/NEW"
        verbose_name_plural = u"优惠券/用户优惠券/NEW"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.customer)
