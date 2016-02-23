# coding= utf-8
"""
模板：负责优惠券的定义（用途，价值，标题）
券池：负责不同优惠券的生成，查询，发放，作废
用户：负责记录用户优惠券持有状态
"""
from django.db import models
import datetime

from .base import PayBaseModel
from options import uniqid
from flashsale.pay.models import Customer


class CouponTemplate(PayBaseModel):
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
    COUPON_TYPE = ((RMB118, u"二期代理优惠券"), (POST_FEE_5, u"5元退货补邮费"),
                   (POST_FEE_10, u"10元退货补邮费"), (POST_FEE_15, u"15元退货补邮费"), (POST_FEE_20, u"20元退货补邮费"),
                   (C150_10, u"满150减10"), (C259_20, u"满259减20"), (DOUBLE_11, u"双11专用"), (DOUBLE_12, u"双12专用"),
                   (USUAL, u"普通"), (NEW_YEAR, u"元旦专用"), (PROMMOTION_TYPE, u"活动类型"))
    CLICK_WAY = 0
    BUY_WAY = 1
    XMM_LINK = 2
    PROMOTION = 3
    COUPON_WAY = ((CLICK_WAY, u"点击方式领取"), (BUY_WAY, u"购买商品获取"),(XMM_LINK, u"购买专属链接"),
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
    preset_days = models.IntegerField(default=0, verbose_name=u"预置天数")
    active_days = models.IntegerField(default=0, verbose_name=u"有效天数")
    use_fee = models.FloatField(default=0.0, verbose_name=u'满单额')  # 满多少可以使用
    bind_pros = models.CharField(max_length=256, null=True, blank=True, verbose_name=u'绑定产品')  # 指定产品可用
    deadline = models.DateTimeField(blank=True, verbose_name=u'截止日期')
    use_notice = models.TextField(blank=True, verbose_name=u"使用须知")
    way_type = models.IntegerField(default=0, choices=COUPON_WAY, verbose_name=u"领取途径")
    target_user = models.IntegerField(default=0, choices=TAR_USER, verbose_name=u"目标用户")
    post_img = models.CharField(max_length=512, blank=True, null=True, verbose_name=u"模板图片")

    class Meta:
        db_table = "pay_coupon_template"
        verbose_name = u"特卖/优惠券/模板/NEW"
        verbose_name_plural = u"优惠券/模板/NEW"

    def __unicode__(self):
        return '<%s,%s>' % (self.id, self.title)

    def template_check(self):
        """ 模板检查 """
        if self.valid != True:
            raise AssertionError(u"无效优惠券")
        else:
            return self

    def usefee_check(self, fee):
        """ 满单额条件检查　"""
        if self.use_fee == 0:
            return
        elif self.use_fee > fee:
            raise AssertionError(u'满%s使用' % self.use_fee)

    def check_date(self):
        """ 检查有效天数　（匹配截止日期）"""
        # 判断当前时间是否在　有效时间内
        now = datetime.datetime.now()
        if now > self.deadline:
            raise AssertionError(u'超过截止日期%s' % self.deadline)
        if self.active_days == 0:  # 没有设置有效时间
            return
        vas_t = self.deadline - datetime.timedelta(days=self.active_days)
        if now < vas_t:
            raise AssertionError(u'%s至%s启动使用' % (vas_t, self.deadline))

    def check_bind_pros(self, product_ids=None):
        """ 检查绑定的产品 """
        tpl_bind_pros = self.bind_pros.strip().split(',') if self.bind_pros else []
        if tpl_bind_pros == []:  # 如果优惠券没有绑定产品
            return
        product_ids = [str(i) for i in product_ids]
        tpl_binds = set(tpl_bind_pros)
        pro_set = set(product_ids)
        if len(tpl_binds & pro_set) == 0:
            raise AssertionError(u'产品不支持使用优惠券')


class CouponsPool(PayBaseModel):
    RELEASE = 1
    UNRELEASE = 0
    PAST = 2
    POOL_COUPON_STATUS = ((RELEASE, u"已发放"), (UNRELEASE, u"未发放"), (PAST, u"已过期"))

    template = models.ForeignKey(CouponTemplate, verbose_name=u"模板ID", null=True, on_delete=models.SET_NULL)
    coupon_no = models.CharField(max_length=32, db_index=True, unique=True, default=lambda: uniqid(
        '%s%s' % ('YH', datetime.datetime.now().strftime('%y%m%d'))), verbose_name=u"优惠券号码")
    status = models.IntegerField(default=UNRELEASE, choices=POOL_COUPON_STATUS, verbose_name=u"发放状态")

    class Meta:
        db_table = "pay_coupon_pool"
        verbose_name = u"特卖/优惠券/券池/NEW"
        verbose_name_plural = u"优惠券/券池/NEW"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.template)

    def coupon_nums(self):
        nums = CouponsPool.objects.filter(template=self.template).count()
        return nums

    def poll_check(self):
        """ 券池检查 """
        if self.status == CouponsPool.UNRELEASE:
            raise AssertionError(u"优惠券没有发放")
        elif self.status == CouponsPool.PAST:
            raise AssertionError(u"优惠券已过期")
        return self

    def past_pool(self):
        """ 过期操作 """
        self.status = self.PAST
        self.save()


class UserCoupon(PayBaseModel):
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
        verbose_name = u"特卖/优惠券/用户优惠券/NEW"
        verbose_name_plural = u"优惠券/用户优惠券/NEW"

    def __unicode__(self):
        return "<%s,%s>" % (self.id, self.customer)

    def coupon_check(self):
        """ 用户优惠券检查 """
        if self.status == self.USED:
            raise AssertionError(u"优惠券已使用")
        elif self.status == self.FREEZE:
            raise AssertionError(u"优惠券已冻结")
        else:
            return self

    def use_coupon(self):
        """ 使用优惠券 """
        self.status = self.USED
        self.save()

    def freeze_coupon(self):
        """ 冻结优惠券 """
        self.status = self.FREEZE
        self.save()

    def unfreeze_coupon(self):
        """ 解冻优惠券 """
        self.status = self.UNUSED
        self.save()

    def check_usercoupon(self, product_ids=None):
        """  验证并检查 用户优惠券 """
        self.cp_id.template.template_check()
        self.cp_id.poll_check()
        self.coupon_check()
        self.cp_id.template.check_date()
        if product_ids is not None:
            self.cp_id.template.check_bind_pros(product_ids=product_ids)
        return

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
                tpl = CouponTemplate.objects.get(id=template_id, valid=True)  # 获取优惠券模板
                start_time = tpl.deadline - datetime.timedelta(days=tpl.preset_days)
                now = datetime.datetime.now()
                if now <= start_time or now >= tpl.deadline:
                    return "not_release"  # 不在模板定义时间
            except CouponTemplate.DoesNotExist:
                return "not_release"
            # 身份判定（判断身份是否和优惠券模板指定用户一致） 注意　这里是硬编码　和　XiaoluMama　代理级别关联
            if tpl.target_user != CouponTemplate.ALL_USER:  # 如果不是所有用户可领取则判定级别
                from flashsale.xiaolumm.models import XiaoluMama

                cus_id = int(buyer_id)
                customer = Customer.objects.get(id=cus_id)
                unionid = customer.unionid
                try:
                    xlmm = XiaoluMama.objects.get(openid=unionid)
                    user_level = xlmm.agencylevel  # 用户的是代理身份 内1 　VIP2  A3
                except XiaoluMama.DoesNotExist:
                    user_level = CouponTemplate.ALL_USER  # 没找到则默认所有用户
            else:
                user_level = CouponTemplate.ALL_USER
            if user_level != tpl.target_user:
                # 如果用户领取的优惠券和用户身份不一致则不予领取
                return "not_release"
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
