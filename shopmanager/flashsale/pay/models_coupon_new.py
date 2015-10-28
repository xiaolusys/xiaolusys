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
    POST_FEE_5 = 1
    POST_FEE_10 = 4
    POST_FEE_15 = 5
    C150_10 = 2
    C259_20 = 3
    COUPON_TYPE = ((RMB118, u"二期代理优惠券"), (POST_FEE_5, u"5元退货补邮费"),
                   (POST_FEE_10, u"10元退货补邮费"), (POST_FEE_15, u"15元退货补邮费"),
                   (C150_10, u"满150减10"), (C259_20, u"满259减20"))

    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")
    value = models.FloatField(default=1.0, verbose_name=u"优惠券价值")
    valid = models.BooleanField(default=False, verbose_name=u"是否有效")
    type = models.IntegerField(choices=COUPON_TYPE, verbose_name=u"优惠券类型")
    nums = models.IntegerField(default=0, verbose_name=u"发放数量")
    limit_num = models.IntegerField(default=1, verbose_name=u"每人领取数量")
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

    template = models.ForeignKey(CouponTemplate, verbose_name=u"模板ID", null=True, on_delete=models.SET_NULL)
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
        return "<%s,%s>" % (self.id, self.template)

    def coupon_nums(self):
        nums = CouponsPool.objects.filter(template=self.template).count()
        return nums


class UserCoupon(models.Model):
    USED = 1
    UNUSED = 0
    FREEZE = 2
    USER_COUPON_STATUS = ((USED, u"已使用"), (UNUSED, u"未使用"), (FREEZE, u"冻结中"))
    """冻结中，领取后多少天后可以使用，即暂时冻结中"""

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

    def release_deposit_coupon(self, **kwargs):
        """
        功能：代理接管的时候生成，优惠券
        """
        buyer_id = kwargs.get("buyer_id", None)
        trade_id = kwargs.get("trade_id", None)
        if buyer_id and trade_id:
            tpl = CouponTemplate.objects.get(type=CouponTemplate.RMB118, valid=True)  # 获取：模板采用admin后台手动产生
            try:
                # 如果该用户发放过则不发放
                UserCoupon.objects.get(customer=buyer_id, cp_id__template__type=CouponTemplate.RMB118)
            except UserCoupon.DoesNotExist:
                cou = CouponsPool.objects.create(template=tpl)  # 生成券池数据
                if cou.coupon_nums() > tpl.nums:  # 发放数量大于定义的数量　抛出异常
                    cou.delete()  # 删除create 防止产生脏数据
                    message = u"{0},优惠券发放数量不能大于模板定义数量.".format(tpl.get_type_display())
                    raise Exception(message)
                else:
                    self.cp_id = cou
                    self.customer = buyer_id
                    self.sale_trade = trade_id
                    self.save()
                    cou.status = CouponsPool.RELEASE  # 发放后，将状态改为已经发放
                    cou.save()
        return

    def release_150_10(self, **kwargs):
        buyer_id = kwargs.get("buyer_id", None)
        # 2015-10-1前可以使用
        trade_id = "0"
        if buyer_id and trade_id:
            tpl = CouponTemplate.objects.get(type=CouponTemplate.C150_10, valid=True)  # 获取满150减10优惠券
            # 每个人只能领取一张
            uc_cs = UserCoupon.objects.filter(customer=buyer_id, cp_id__template__type=CouponTemplate.C150_10)
            if uc_cs.count() >= tpl.limit_num:  # 如果大于定义的限制领取数量
                return "limit"
            else:
                # 发放优惠券
                cou = CouponsPool.objects.create(template=tpl)  # 生成券池数据
                if cou.coupon_nums() > tpl.nums:  # 发放数量大于定义的数量　抛出异常
                    cou.delete()  # 删除create 防止产生脏数据
                    message = u"{0},优惠券发放数量不能大于模板定义数量.".format(tpl.get_type_display())
                    raise Exception(message)
                else:
                    self.cp_id = cou
                    self.customer = buyer_id
                    self.sale_trade = trade_id
                    self.save()
                    cou.status = CouponsPool.RELEASE  # 发放后，将状态改为已经发放
                    cou.save()
                    return "success"
        return None

    def release_259_20(self, **kwargs):
        buyer_id = kwargs.get("buyer_id", None)
        # 2015-10-1前可以使用
        trade_id = "0"
        if buyer_id and trade_id:
            tpl = CouponTemplate.objects.get(type=CouponTemplate.C259_20, valid=True)  # 获取满150减10优惠券
            # 每个人只能领取一张
            uc_cs = UserCoupon.objects.filter(customer=buyer_id, cp_id__template__type=CouponTemplate.C259_20)
            if uc_cs.count() >= tpl.limit_num:  # 如果大于定义的限制领取数量
                return "limit"
            cou = CouponsPool.objects.create(template=tpl)  # 生成券池数据
            if cou.coupon_nums() > tpl.nums:  # 发放数量大于定义的数量　抛出异常
                cou.delete()  # 删除create 防止产生脏数据
                message = u"{0},优惠券发放数量不能大于模板定义数量.".format(tpl.get_type_display())
                raise Exception(message)
            else:
                self.cp_id = cou
                self.customer = buyer_id
                self.sale_trade = trade_id
                self.save()
                cou.status = CouponsPool.RELEASE  # 发放后，将状态改为已经发放
                cou.save()
                return "success"
        return None

    def release_by_template(self, **kwargs):
        """
        发放不绑定交易的任何类型的优惠券
        """
        buyer_id = kwargs.get("buyer_id", None)
        template_id = kwargs.get("template_id", None)
        trade_id = kwargs.get("trade_id", '0')
        # {"buyer_id": customer.id, "template_id":template_id}
        if buyer_id and trade_id and template_id:
            try:
                tpl = CouponTemplate.objects.get(id=template_id, valid=True)  # 获取满150减10优惠券
            except CouponTemplate.DoesNotExist:
                return "not_release"
            # 每个人只能领取一张
            uc_cs = UserCoupon.objects.filter(customer=buyer_id, cp_id__template__id=template_id)
            if uc_cs.count() >= tpl.limit_num:  # 如果大于定义的限制领取数量
                return "limit"
            cou = CouponsPool.objects.create(template=tpl)  # 生成券池数据
            if cou.coupon_nums() > tpl.nums:  # 发放数量大于定义的数量　抛出异常
                cou.delete()  # 删除create 防止产生脏数据
                message = u"{0},优惠券发放数量不能大于模板定义数量.".format(tpl.get_type_display())
                raise Exception(message)
            else:
                self.cp_id = cou
                self.customer = buyer_id
                self.sale_trade = trade_id
                self.save()
                cou.status = CouponsPool.RELEASE  # 发放后，将状态改为已经发放
                cou.save()
                return "success"
        return None