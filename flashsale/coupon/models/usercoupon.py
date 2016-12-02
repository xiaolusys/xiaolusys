# coding=utf-8
import datetime
from core.models import BaseModel
from django.db import models
from flashsale.pay.options import uniqid
from core.fields import JSONCharMyField
from .managers.usercoupon import UserCouponManager


def default_coupon_no():
    # type: () -> text_type
    return uniqid('%s%s' % ('yhq', datetime.datetime.now().strftime('%y%m%d')))


def default_coupon_extras():
    # type: () -> Dict[str, Any]
    return {'user_info': {'id': None, 'nick': '', 'thumbnail': ''}}


class UserCoupon(BaseModel):
    TYPE_NORMAL = 1
    TYPE_ORDER_SHARE = 2
    TYPE_MAMA_INVITE = 3
    TYPE_COMPENSATE = 4
    TYPE_ORDER_BENEFIT = 5
    TYPE_ACTIVE_SHARE = 6
    TYPE_CASHOUT_EXCHANGE = 7
    TYPE_TRANSFER = 8

    COUPON_TYPES = (
        (TYPE_NORMAL, u"普通类型"),  # 一般点击类型,或者普通发放类型
        (TYPE_ORDER_BENEFIT, u"下单红包"),  # 用户购买商品后发放
        (TYPE_ORDER_SHARE, u"订单分享"),  # 用户购买商品后分享给其他人领取
        (TYPE_MAMA_INVITE, u"推荐专享"),  # 在代理的专属链接购买商品后,给代理发放的类型
        (TYPE_COMPENSATE, u"售后补偿"),  # 不邮费等售后服务发放
        (TYPE_ACTIVE_SHARE, u"活动分享"),  # 不邮费等售后服务发放
        (TYPE_CASHOUT_EXCHANGE, u"提现兑换"),  # 提现兑换类型
        (TYPE_TRANSFER, u"精品专用券")
    )

    UNUSED = 0
    USED = 1
    FREEZE = 2
    PAST = 3
    CANCEL = 4  # 不该发而发了之后回退操作，算。
    USER_COUPON_STATUS = ((UNUSED, u"未使用"), (USED, u"已使用"), (FREEZE, u"冻结中"), (PAST, u"已经过期"), (CANCEL, u'已经取消'))

    WX = u'wx'
    PYQ = u'pyq'
    QQ = u'qq'
    QQ_SPA = u'qq_spa'
    SINA = u'sina'
    WAP = u'wap'
    TMP = u'tmp'
    PLATFORM = ((WX, u"微信好友"),
                (PYQ, u"朋友圈"),
                (QQ, u"QQ好友"),
                (QQ_SPA, u"QQ空间"),
                (SINA, u"新浪微博"),
                (WAP, u'wap'),
                (TMP, u'临时表'))

    template_id = models.IntegerField(db_index=True, verbose_name=u"优惠券id")  # type: int
    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")  # type: text_type
    coupon_type = models.IntegerField(default=TYPE_NORMAL, choices=COUPON_TYPES, verbose_name=u"优惠券类型")  # type: int

    customer_id = models.IntegerField(db_index=True, verbose_name=u"顾客ID")  # type: int
    share_user_id = models.IntegerField(db_index=True, blank=True, null=True,
                                        verbose_name=u"分享用户ID")  # type: Optional[int]
    order_coupon_id = models.IntegerField(db_index=True, blank=True, null=True,
                                          verbose_name=u"订单优惠券分享ID")  # type: Optional[int]

    coupon_no = models.CharField(max_length=32, unique=True,
                                 default=default_coupon_no, verbose_name=u"优惠券号码")  # type: text_type
    value = models.FloatField(verbose_name=u"优惠券价值")  # type: float

    trade_tid = models.CharField(max_length=32, db_index=True, blank=True, null=True,
                                 verbose_name=u"绑定交易tid")  # type: Optional[text_type]
    # finished_time 保存优惠券被使用掉的时间
    finished_time = models.DateTimeField(db_index=True, blank=True, null=True,
                                         verbose_name=u"使用时间")  # type: Optional[datetime.datetime]
    start_use_time = models.DateTimeField(db_index=True, verbose_name=u"开始时间")  # type: Optional[datetime.datetime]
    expires_time = models.DateTimeField(db_index=True, verbose_name=u"过期时间")  # type: Optional[datetime.datetime]

    ufrom = models.CharField(max_length=8, choices=PLATFORM, db_index=True, blank=True,
                             verbose_name=u'领取平台')  # type: text_tpe
    uniq_id = models.CharField(unique=True, max_length=32,  # template_id_customer_id_order_coupon_id_(number_of_tpl)
                               verbose_name=u"优惠券唯一标识")  # type: text_type
    status = models.IntegerField(default=UNUSED, choices=USER_COUPON_STATUS, verbose_name=u"使用状态")  # type: int
    is_pushed = models.BooleanField(default=False, db_index=True, verbose_name=u'是否推送')  # type: bool
    extras = JSONCharMyField(max_length=1024, default=default_coupon_extras, blank=True, null=True,
                             verbose_name=u"附加信息")  # type: text_type
    objects = UserCouponManager()

    class Meta:
        db_table = "flashsale_user_coupon"
        app_label = 'coupon'
        index_together = ['status', 'template_id']
        verbose_name = u"特卖/优惠券/用户优惠券表"
        verbose_name_plural = u"特卖/优惠券/用户优惠券列表"

    def __unicode__(self):
        # type: () -> text_type
        return "<%s,%s>" % (self.id, self.customer_id)

    @property
    def customer(self):
        # type: () -> Optional[Customer]
        if not hasattr(self, '_coupon_customer_'):
            from flashsale.pay.models import Customer

            self._coupon_customer_ = Customer.objects.normal_customer.filter(id=self.customer_id).first()
        return self._coupon_customer_

    def is_transfer_coupon(self):
        from .coupon_template import CouponTemplate

        ct = CouponTemplate.objects.filter(id=self.template_id).first()
        return ct and ct.coupon_type == CouponTemplate.TYPE_TRANSFER

    def self_template(self):
        # type: () -> CouponTemplate
        from flashsale.coupon.models import CouponTemplate

        return CouponTemplate.objects.get(id=self.template_id)

    def share_record(self):
        # type: () -> Optional[OrderShareCoupon]
        """ 优惠券来自与那个分享(如果是从分享来的话) """
        from .ordershare_coupon import OrderShareCoupon

        return OrderShareCoupon.objects.filter(id=self.order_coupon_id).first()

    def is_valid_template(self):
        # type: () -> bool
        """ 模板有效性 """
        tpl = self.self_template()
        return True if tpl.template_valid_check() else False

    def min_payment(self):
        # type: () -> float
        """ 最低使用费用(满单额) """
        tpl = self.self_template()
        return tpl.use_min_payment

    def coupon_use_fee_des(self):
        # type: () -> text_type
        """ 满单额描述 """
        min_payment = self.min_payment()
        return u"满%s可用" % min_payment

    def scope_type_desc(self):
        # type: () -> text_type
        """ 使用范围描述 """
        tpl = self.self_template()
        return tpl.get_scope_type_display()

    def user_nick_name(self):
        # type: () -> text_type
        """ 用户昵称 """
        return self.extras['user_info']['nick']

    def user_head_img(self):
        # type: () -> text_type
        """ 用户头像 """
        return self.extras['user_info']['thumbnail']

    @property
    def transfer_coupon_pk(self):
        # type: () -> Optional[text_type]
        return self.extras.get('transfer_coupon_pk')

    def coupon_basic_check(self):
        # type: () -> UserCoupon
        """
        日期检测 & 状态检查
        """
        now = datetime.datetime.now()
        coupon = self.__class__.objects.get(id=self.id)
        if coupon.status == UserCoupon.USED:
            raise AssertionError(u"优惠券已使用")
        elif coupon.status == UserCoupon.FREEZE:
            raise AssertionError(u"优惠券已冻结")
        elif coupon.status == UserCoupon.PAST:
            raise AssertionError(u"优惠券已过期")
        if not (now <= coupon.expires_time):
            raise AssertionError(u"使用日期错误")
        return coupon

    def check_user_coupon(self, product_ids=None, use_fee=None):
        # type: (List[int], float) -> None
        """  用户优惠券检查是否可用 """
        from flashsale.coupon.models import CouponTemplate

        tpl = CouponTemplate.objects.get(id=self.template_id)
        tpl.check_bind_pros(product_ids=product_ids)  # 绑定产品检查
        tpl.template_valid_check()  # 模板有效性检查
        tpl.usefee_check(use_fee)  # 优惠券状态检查
        self.coupon_basic_check()  # 基础检查
        return

    def freeze_coupon(self):
        # type: () -> None
        """ 冻结优惠券 """
        coupon = self.__class__.objects.get(id=self.id)
        if coupon.status != UserCoupon.UNUSED:
            raise AssertionError(u"优惠券不在未使用状态,冻结失败")
        self.status = self.FREEZE
        self.save()

    def unfreeze_coupon(self):
        # type: () -> None
        """ 解冻优惠券 """
        coupon = self.__class__.objects.get(id=self.id)
        if coupon.status != UserCoupon.FREEZE:
            raise AssertionError(u"优惠券不在冻结状态,解冻出错")
        self.status = self.UNUSED
        self.save()

    def get_pool_status(self):
        # type: () -> int
        """ 临时使用(ios接口兼容使用) """
        if self.status == UserCoupon.UNUSED:
            return 1
        return 2
