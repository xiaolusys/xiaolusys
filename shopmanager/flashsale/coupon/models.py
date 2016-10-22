# coding=utf-8
"""
模板：负责优惠券的定义（用途，价值，标题） 普通类型模板只能领取一张
分享批次：负责分享时候生成批次记录,绑定交易,用户,使用模板
用户：负责记录用户优惠券持有状态,使用价值等信息
"""
import datetime
import random
from django.db import models
from django.db.models.signals import post_save, pre_save
from flashsale.coupon import tasks
from flashsale.pay.options import uniqid
from core.models import BaseModel
from core.fields import JSONCharMyField
from flashsale.coupon.managers import UserCouponManager
from managers import OrderShareCouponManager


def default_template_extras():
    # type: () -> Dict[str, Any]
    return {
        'release': {
            'use_min_payment': 500,  # 满多少可以使用
            'release_min_payment': 50,  # 满多少可以发放
            'use_after_release_days': 0,  # 发放多少天后可用
            'limit_after_release_days': 30,  # 发放多少天内可用
            'share_times_limit': 20  # 分享链接被成功领取的优惠券次数
        },
        'randoms': {'min_val': 0, 'max_val': 1},  # 随机金额范围
        'scopes': {'product_ids': '', 'category_ids': ''},  # 使用范围
        'templates': {'post_img': ''}  # 优惠券模板
    }

def get_choice_name(choices, val):
    """
    iterate over choices and find the name for this val
    """
    name = ""
    for entry in choices:
        if entry[0] == val:
            name = entry[1]
    return name

class CouponTemplate(BaseModel):
    """ 优惠券模板 """

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
        (TYPE_TRANSFER, u"可流通精品券")
    )

    TARGET_ALL = 1
    TARGET_VIP = 2
    TARGET_A = 3
    # 这里注意下类型对应在xiaolumm模块的代理级别
    TARGET_TYPES = ((TARGET_ALL, u"所有用户"),
                    (TARGET_VIP, u"VIP类代理"),
                    (TARGET_A, u"A类代理"))

    SCOPE_OVERALL = 1
    SCOPE_CATEGORY = 2
    SCOPE_PRODUCT = 3
    SCOPE_TYPES = ((SCOPE_OVERALL, u"全场通用"),
                   (SCOPE_CATEGORY, u"类目专用"),
                   (SCOPE_PRODUCT, u"商品专用"))

    CREATE = 0
    SENDING = 1
    FINISHED = 2
    CANCEL = 3
    STATUS_CHOICES = ((CREATE, u'未发放'),  # 定义模板后没有发放 待用
                      (SENDING, u'发放中'),  # 模板正在使用中
                      (FINISHED, u'已结束'),  # 正常发放后结束发放
                      (CANCEL, u'已取消'),)  # 发放中到取消状态取消发放

    title = models.CharField(max_length=64, verbose_name=u"优惠券标题")  # type: text_type
    description = models.CharField(max_length=128, verbose_name=u"使用说明")  # type: text_type
    value = models.FloatField(default=1.0, verbose_name=u"优惠券价值")  # type: float

    is_random_val = models.BooleanField(default=False, db_index=True, verbose_name=u"金额随机")  # type: bool
    prepare_release_num = models.IntegerField(default=0, verbose_name=u"计划发放数量")  # type: int
    is_flextime = models.BooleanField(default=False, db_index=True, verbose_name=u"弹性有效时间")  # type: bool

    release_start_time = models.DateTimeField(blank=True, null=True,
                                              verbose_name=u'开始发放的时间')  # type: Optional[datetime.datetime]
    release_end_time = models.DateTimeField(blank=True, null=True,
                                            verbose_name=u'结束发放的时间')  # type: Optional[datetime.datetime]
    use_deadline = models.DateTimeField(blank=True, null=True,
                                        verbose_name=u'截止使用的时间')  # type: Optional[datetime.datetime]

    has_released_count = models.IntegerField(default=0, verbose_name=u"已领取数量")  # type: int
    has_used_count = models.IntegerField(default=0, verbose_name=u"已使用数量")  # type: int

    coupon_type = models.IntegerField(default=TYPE_NORMAL, choices=COUPON_TYPES, verbose_name=u"优惠券类型")  # type: int
    target_user = models.IntegerField(default=TARGET_ALL, choices=TARGET_TYPES, verbose_name=u"目标用户")  # type: int
    scope_type = models.IntegerField(default=SCOPE_OVERALL, choices=SCOPE_TYPES, verbose_name=u"使用范围")  # type: int

    status = models.IntegerField(default=CREATE, choices=STATUS_CHOICES, verbose_name=u"状态")  # type: int
    extras = JSONCharMyField(max_length=512, blank=True, null=True, default=default_template_extras,
                             verbose_name=u"附加信息")  # type: text_type

    class Meta:
        db_table = "flashsale_coupon_template"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/模板"
        verbose_name_plural = u"特卖/优惠券/模板列表"

    def __unicode__(self):
        # type: () -> text_type
        return '<%s,%s>' % (self.id, self.title)

    @property
    def share_times_limit(self):
        # type: () -> int
        return self.extras['release']['share_times_limit']

    @property
    def post_img(self):
        # type: () -> text_type
        return self.extras['templates']['post_img']

    @property
    def limit_after_release_days(self):
        # type: () -> int
        """ 发放后多少天内可用 """
        return self.extras['release']['limit_after_release_days']

    @property
    def use_after_release_days(self):
        # type: () -> int
        """ 发放多少天后可用 """
        return self.extras['release']['use_after_release_days']

    @property
    def use_min_payment(self):
        # type: () -> float
        """ 最低购买金额 """
        return self.extras['release']['use_min_payment']

    @property
    def bind_category_ids(self):
        # type: () -> text_type
        """ 绑定产品类目 """
        return self.extras['scopes']['category_ids']

    @property
    def bind_product_ids(self):
        # type: () -> text_type
        """ 绑定产品产品 """
        return self.extras['scopes']['product_ids']

    @property
    def min_val(self):
        # type: () -> int
        """ 随机最小值 """
        return self.extras['randoms']['min_val']

    @property
    def max_val(self):
        # type: () -> int
        """ 随机最大值 """
        return self.extras['randoms']['max_val']

    def template_valid_check(self):
        # type: () -> CouponTemplate
        """
        模板检查, 不在发放中 和发放结束状态的优惠券视为无效优惠券
        """
        if self.status not in (CouponTemplate.SENDING, CouponTemplate.FINISHED):
            raise AssertionError(u"无效优惠券")
        return self

    def template_valid(self):
        # type: () -> bool
        """ 模板是否有效 """
        if self.status in (CouponTemplate.SENDING, CouponTemplate.FINISHED):
            return True
        return False

    def use_fee_desc(self):
        # type: () -> text_type
        """ 满单额描述 """
        return "满{0}可用".format(self.use_min_payment)

    def usefee_check(self, fee):
        # type: (float) -> None
        """
        满单额条件检查　
        :param fee 交易金额
        """
        if self.use_min_payment == 0:
            return
        elif self.use_min_payment > fee:
            raise AssertionError(u'该优惠券满%s元可用' % self.use_min_payment)

    def check_date(self):
        # type: () -> None
        """ 检查有效天数（匹配截止日期） 返回有效的开始时间和结束时间 """
        # 判断当前时间是否在　有效时间内
        now = datetime.datetime.now()
        if self.release_start_time <= now <= self.use_deadline:
            return  # 在正常时间内
        raise AssertionError(u'%s至%s开放' % (self.release_start_time, self.release_end_time))

    def check_category(self, product_ids=None):
        # type: (List[int]) -> None
        """ 可用分类检查 """
        category_ids = self.bind_category_ids
        if not category_ids:  # 没有设置分类限制信息　则为全部分类可以使用
            return
        from shopback.items.models import Product

        tpl_categorys = category_ids.strip().split(',') if category_ids else []

        buy_pros_categorys = Product.objects.filter(id__in=product_ids).values('category_id')
        buy_category_ids = [str(i['category_id']) for i in buy_pros_categorys]

        set_tpl_categorys = set(tpl_categorys)
        set_category = set(buy_category_ids)
        if len(set_tpl_categorys & set_category) == 0:  # 比较分类 如果没有存在的分类则报错
            raise AssertionError(u'该品类不支持使用优惠券')
        return

    def check_bind_pros(self, product_ids=None):
        # type: (List[int]) -> None
        """ 检查绑定的产品 """
        from shopback.items.models import Product
        from flashsale.pay.models import ModelProduct

        model_ids = list(Product.objects.filter(id__in=product_ids).values_list('model_id', flat=True))
        model_products = ModelProduct.objects.filter(id__in=model_ids).only('extras')
        is_coupon_allow = reduce(lambda x, y: x | y, [not mp.is_coupon_deny for mp in model_products])
        if not is_coupon_allow:
            raise AssertionError(u'该产品不支持使用优惠券')

        tpl_product_ids = self.bind_product_ids  # 设置的绑定的产品
        tpl_bind_pros = tpl_product_ids.strip().split(',') if tpl_product_ids else []  # 绑定的产品list
        if not tpl_bind_pros != []:  # 如果优惠券没有绑定产品
            self.check_category(product_ids)  # 没有限制产品则检查分类限制
            return
        product_str_ids = [str(i) for i in product_ids]
        tpl_binds = set(tpl_bind_pros)
        pro_set = set(product_str_ids)
        if len(tpl_binds & pro_set) == 0:
            raise AssertionError(u'该产品不支持使用优惠券')
        # 检查产品后检查分类(检查设置了绑定产品并且绑定了类目的情况)
        self.check_category(product_ids)

    def can_send(self):
        # type: () -> bool
        coupons = UserCoupon.objects.filter(template_id=self.id)
        tpl_release_count = coupons.count()  # 当前模板的优惠券条数
        return tpl_release_count < self.prepare_release_num and self.status == CouponTemplate.SENDING

    def make_uniq_id(tpl, customer_id, trade_id=None, share_id=None, refund_trade_id=None, cashout_id=None):
        # type: (CouponTemplate, int, Any, Any, Any, Any) -> text_type
        uniqs = [str(tpl.id), str(tpl.coupon_type), str(customer_id)]
        if tpl.coupon_type == CouponTemplate.TYPE_NORMAL:  # 普通类型 1
            uniqs = uniqs

        elif tpl.coupon_type == CouponTemplate.TYPE_ORDER_BENEFIT and trade_id:  # 下单红包 2
            uniqs.append(str(trade_id))

        elif tpl.coupon_type == CouponTemplate.TYPE_ORDER_SHARE and share_id:  # 订单分享 3
            uniqs.append(str(share_id))

        elif tpl.coupon_type == CouponTemplate.TYPE_MAMA_INVITE and trade_id:  # 推荐专享 4
            uniqs.append(str(trade_id))  # 一个专属链接可以有多个订单

        elif tpl.coupon_type == CouponTemplate.TYPE_COMPENSATE and refund_trade_id:  # 售后补偿 5
            uniqs.append(str(refund_trade_id))

        elif tpl.coupon_type == CouponTemplate.TYPE_ACTIVE_SHARE and share_id:  # 活动分享 6
            uniqs.append(str(share_id))

        elif tpl.coupon_type == CouponTemplate.TYPE_CASHOUT_EXCHANGE and cashout_id:  # 优惠券兑换　7
            uniqs.append(str(cashout_id))
        else:
            raise Exception('Template type is tpl.coupon_type : %s !' % tpl.coupon_type)
        return '_'.join(uniqs)

    def gen_usercoupon_unikey(self, order_id, index=0):
        # type: (int, int) -> text_type
        """生成对应优惠券的unique key
        """
        return "%s_%s_%s_%s" % (self.id, self.coupon_type, order_id, index)

    def calculate_value_and_time(self):
        # type: (CouponTemplate) -> Tuple[float, datetime.datetime, datetime.datetime]
        """计算发放优惠券价值和开始使用时间和结束时间
        """
        value = self.value  # 默认取模板默认值
        if self.is_random_val and self.min_val and self.max_val:  # 如果设置了随机值则选取随机值
            value = float('%.1f' % random.uniform(self.max_val, self.min_val))  # 生成随机的value

        expires_time = self.use_deadline
        start_use_time = datetime.datetime.now()
        if self.is_flextime:  # 如果是弹性时间
            # 断言设置弹性时间的时候 仅仅设置一个 定制日期  否则报错
            assert (self.limit_after_release_days == 0 or self.use_after_release_days == 0)
            if self.limit_after_release_days:  # 发放后多少天内可用 days 使用时间即 领取时间 过期时间为领取时间+ days
                expires_time = start_use_time + datetime.timedelta(days=self.limit_after_release_days)
            if self.use_after_release_days:  # 发放多少天后可用 即开始时间 为 模板开始发放的时间+use_after_release_days
                start_use_time = start_use_time + datetime.timedelta(days=self.use_after_release_days)
                expires_time = self.use_deadline
            assert (start_use_time < expires_time)  # 断言开始时间 < 结束时间
        return value, start_use_time, expires_time


def default_share_extras():
    # type: () -> Dict[str, Any]
    return {
        'user_info': {'id': None, 'nick': '', 'thumbnail': ''},
        "templates": {"post_img": '', "description": '', "title": ''}
    }


class OrderShareCoupon(BaseModel):
    WX = u'wx'
    PYQ = u'pyq'
    QQ = u'qq'
    QQ_SPA = u'qq_spa'
    SINA = u'sina'
    WAP = u'wap'
    PLATFORM = ((WX, u"微信好友"), (PYQ, u"朋友圈"), (QQ, u"QQ好友"),
                (QQ_SPA, u"QQ空间"), (SINA, u"新浪微博"), (WAP, u'wap'))
    SENDING = 0
    FINISHED = 1
    STATUS_CHOICES = (
        (SENDING, u'发放中'),
        (FINISHED, u'已结束'))
    template_id = models.IntegerField(db_index=True, verbose_name=u"模板ID")  # type: int
    share_customer = models.IntegerField(db_index=True, verbose_name=u'分享用户')  # type: int
    uniq_id = models.CharField(max_length=32, unique=True, verbose_name=u"唯一ID")  # type: text_type  # 交易的tid

    release_count = models.IntegerField(default=0, verbose_name=u"领取次数")  # type: int  # 该分享下 优惠券被领取成功次数
    has_used_count = models.IntegerField(default=0, verbose_name=u"使用次数")  # type: int  # 该分享下产生优惠券被使用的次数
    limit_share_count = models.IntegerField(default=0, verbose_name=u"最大领取次数")  # type: int

    platform_info = JSONCharMyField(max_length=128, blank=True, default='{}',
                                    verbose_name=u"分享到平台记录")  # type: text_type
    share_start_time = models.DateTimeField(blank=True, verbose_name=u"分享开始时间")  # type: Optional[datetime.datetime]
    share_end_time = models.DateTimeField(blank=True, db_index=True,
                                          verbose_name=u"分享截止时间")  # type: Optional[datetime.datetime]

    # 用户点击分享的时候 判断如果达到最大分享次数了 修改该状态到分享结束
    status = models.IntegerField(default=SENDING, db_index=True, choices=STATUS_CHOICES,
                                 verbose_name=u"状态")  # type: int
    extras = JSONCharMyField(max_length=1024, default=default_share_extras, blank=True, null=True,
                             verbose_name=u"附加信息")  # type: Optional[text_type]
    objects = OrderShareCouponManager()

    class Meta:
        db_table = "flashsale_coupon_share_batch"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/订单分享表"
        verbose_name_plural = u"特卖/优惠券/订单分享列表"

    def __unicode__(self):
        # type: () -> text_type
        return "<%s,%s>" % (self.id, self.template_id)

    @property
    def nick(self):
        # type: () -> text_type
        """分享者昵称"""
        return self.extras['user_info']['nick']

    @property
    def thumbnail(self):
        # type: () -> text_type
        """分享者的头像"""
        return self.extras['user_info']['thumbnail']

    @property
    def post_img(self):
        # type: () -> text_type
        """模板的图片链接"""
        return self.extras['templates']['post_img']

    @property
    def description(self):
        # type: () -> text_type
        """模板的描述"""
        return self.extras['templates']['description']

    @property
    def title(self):
        # type: () -> text_type
        """模板的标题"""
        return self.extras['templates']['title']

    @property
    def template(self):
        # type: () -> Optional[CouponTemplate]
        return CouponTemplate.objects.filter(id=self.template_id).first()

    @property
    def remain_num(self):
        # type: () -> int
        """ 还剩下多少次没领取 """
        return self.limit_share_count - self.release_count


def coupon_share_xlmm_newtask(sender, instance, **kwargs):
    # type: (Any, Any, **Any) -> None
    """
    检测新手任务：分享第一个红包
    """
    from flashsale.xiaolumm.tasks_mama_push import task_push_new_mama_task
    from flashsale.xiaolumm.models.new_mama_task import NewMamaTask
    from flashsale.pay.models.user import Customer

    coupon_share = instance
    customer_id = coupon_share.share_customer
    customer = Customer.objects.filter(id=customer_id).first()
    if not customer:
        return

    xlmm = customer.getXiaolumm()
    coupon_share = OrderShareCoupon.objects.filter(share_customer=customer_id).exists()

    if xlmm and not coupon_share:
        task_push_new_mama_task.delay(xlmm, NewMamaTask.TASK_FIRST_SHARE_COUPON)


pre_save.connect(coupon_share_xlmm_newtask,
                 sender=OrderShareCoupon, dispatch_uid='pre_save_coupon_share_xlmm_newtask')


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

    def self_template(self):
        # type: () -> CouponTemplate
        return CouponTemplate.objects.get(id=self.template_id)

    def share_record(self):
        # type: () -> Optional[OrderShareCoupon]
        """ 优惠券来自与那个分享(如果是从分享来的话) """
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
        tpl = CouponTemplate.objects.get(id=self.template_id)
        tpl.check_bind_pros(product_ids=product_ids)  # 绑定产品检查
        tpl.template_valid_check()  # 模板有效性检查
        tpl.usefee_check(use_fee)  # 优惠券状态检查
        self.coupon_basic_check()  # 基础检查
        return

    def use_coupon(self, trade_tid):
        # type: (text_type) -> None
        """ 使用优惠券 """
        from flashsale.coupon.tasks import task_update_coupon_use_count

        coupon = self.__class__.objects.get(id=self.id)
        coupon.coupon_basic_check()  # 基础检查
        coupon.status = self.USED
        coupon.save()
        task_update_coupon_use_count.delay(coupon, trade_tid)

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

    def release_usercoupon(self):
        # type: () -> bool
        """ 优惠券状态从使用状态改为未使用 """
        if self.status == UserCoupon.USED:
            self.status = UserCoupon.UNUSED
            self.save(update_fields=['status'])
            return True
        return False

    @staticmethod
    def send_coupon(customer, tpl, ufrom='wap', uniq_id=None):
        # type: (Customer, CouponTemplate, text_type) -> UserCoupon
        if not tpl.can_send():
            raise Exception(u'优惠券已发送完毕')
        uniq_id = tpl.make_uniq_id(customer.id) if uniq_id is None else uniq_id
        value, start_use_time, expires_time = tpl.calculate_value_and_time()
        extras = {'user_info': {'id': customer.id, 'nick': customer.nick, 'thumbnail': customer.thumbnail}}
        cou = UserCoupon.objects.filter(uniq_id=uniq_id).first()
        if cou:
            raise Exception(u'优惠券已发送过')
        cou = UserCoupon.objects.create(template_id=tpl.id,
                                        title=tpl.title,
                                        coupon_type=tpl.coupon_type,
                                        customer_id=customer.id,
                                        value=value,
                                        start_use_time=start_use_time,
                                        expires_time=expires_time,
                                        ufrom=ufrom,
                                        uniq_id=uniq_id,
                                        extras=extras)
        # update the release num
        tasks.task_update_tpl_released_coupon_nums.delay(tpl)
        return cou

    @classmethod
    def create_salerefund_post_coupon(cls, buyer_id, trade_id, money):
        # type: (int, int, float) -> UserCoupon
        tpl = CouponTemplate.objects.filter(coupon_type=CouponTemplate.TYPE_COMPENSATE,
                                            value=money, status=CouponTemplate.SENDING).first()
        template_id = tpl.id if tpl else 0
        return cls.objects.create_refund_post_coupon(buyer_id, template_id, trade_id)


# 注释代码:  2016-9-30
# def update_unionid_download_record(sender, instance, created, **kwargs):
# if instance.coupon_type != UserCoupon.TYPE_ORDER_SHARE:  # 非订单分享类型
# return
# from flashsale.coupon.tasks import task_update_unionid_download_record
#
# task_update_unionid_download_record.delay(instance)
#
#
# post_save.connect(update_unionid_download_record, sender=UserCoupon,
# dispatch_uid='post_save_update_unionid_download_record')


class TmpShareCoupon(BaseModel):
    mobile = models.CharField(max_length=11, db_index=True, verbose_name=u'手机号')  # type: text_type
    share_coupon_id = models.CharField(db_index=True, max_length=32, verbose_name=u"分享uniq_id")  # type: text_type
    status = models.BooleanField(default=False, db_index=True, verbose_name=u'是否领取')  # type: bool
    value = models.FloatField(default=0.0, verbose_name=u'优惠券价值')  # type: float

    class Meta:
        unique_together = ('mobile', 'share_coupon_id')  # 一个分享 一个手机号只能领取一次
        db_table = "flashsale_user_tmp_coupon"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/用户临时优惠券表"
        verbose_name_plural = u"特卖/优惠券/用户临时优惠券列表"

    def __unicode__(self):
        # type: () -> text_type
        return "<%s,%s>" % (self.id, self.mobile)


def update_mobile_download_record(sender, instance, created, **kwargs):
    # type: (Any, TmpShareCoupon, bool, **Any) -> None
    from flashsale.coupon.tasks import task_update_mobile_download_record

    task_update_mobile_download_record.delay(instance)


post_save.connect(update_mobile_download_record, sender=TmpShareCoupon,
                  dispatch_uid='post_save_update_mobile_download_record')


class CouponTransferRecord(BaseModel):
    TEMPLATE_ID = 153
    COUPON_VALUE = 128
    MAX_DAILY_TRANSFER = 60 # 每天两人间最大流通次数:60次
        
    OUT_CASHOUT = 1 #退券换钱/out
    OUT_TRANSFER = 2 #转给下属/out
    OUT_CONSUMED = 3 #直接买货/out
    IN_BUY_COUPON = 4 #花钱买券/in
    IN_RETURN_COUPON = 5 #下属退券/in
    IN_RETURN_GOODS = 6 #退货退券/in
    TRANSFER_TYPES = ((OUT_CASHOUT, u'退券换钱'),(OUT_TRANSFER, u'转给下属'),(OUT_CONSUMED, u'直接买货'),
                      (IN_BUY_COUPON, u'花钱买券'),(IN_RETURN_COUPON, u'下属退券'),(IN_RETURN_GOODS, u'退货退券'))
    
    PENDING = 1
    PROCESSED = 2
    DELIVERED = 3
    CANCELED = 4
    TRANSFER_STATUS = ((PENDING, u'待审核'), (PROCESSED, u'待发送'), (DELIVERED, u'已完成'), (CANCELED, u'已取消'),)
    
    EFFECT = 1
    CANCEL = 2
    STATUS_TYPES = ((EFFECT, u'有效'), (CANCEL, u'无效'), )

    # Note: 
    # The design follows the route that a coupon is transfered from an agency (coupon_from_mama_id) to
    # another agency (coupon_to_mama_id).
    # 
    coupon_from_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'源头妈妈ID')
    from_mama_thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'源头妈妈头像')
    from_nama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'源头妈妈昵称')

    coupon_to_mama_id = models.IntegerField(default=0, db_index=True, verbose_name=u'终点妈妈ID')
    to_mama_thumbnail = models.CharField(max_length=256, blank=True, verbose_name=u'终点妈妈头像')
    to_nama_nick = models.CharField(max_length=64, blank=True, verbose_name=u'终点妈妈昵称')
    
    template_id = models.IntegerField(default=TEMPLATE_ID, db_index=True, verbose_name=u'优惠券模版')
    coupon_value = models.IntegerField(default=COUPON_VALUE, verbose_name=u'面额')
    coupon_num = models.IntegerField(default=0, verbose_name=u'数量')
    transfer_type = models.IntegerField(default=0, db_index=True, choices=TRANSFER_TYPES, verbose_name=u'流通类型')
    transfer_status = models.IntegerField(default=1, db_index=True, choices=TRANSFER_STATUS, verbose_name=u'流通状态')
    status = models.IntegerField(default=1, db_index=True, choices=STATUS_TYPES, verbose_name=u'状态')
    uni_key = models.CharField(max_length=128, blank=True, unique=True, verbose_name=u'唯一ID')
    date_field = models.DateField(default=datetime.date.today, db_index=True, verbose_name=u'日期')
        
    class Meta:
        db_table = "flashsale_coupon_transfer_record"
        app_label = 'coupon'
        verbose_name = u"特卖/精品券流通记录"
        verbose_name_plural = u"特卖/精品券流通记录表"

    @classmethod
    def gen_unikey(cls, from_mama_id, to_mama_id, template_id, date_field):
        # from_mama_id + to_mama_id + template_id + date_field + idx
        idx = cls.objects.filter(coupon_from_mama_id=from_mama_id,coupon_to_mama_id=to_mama_id,template_id=template_id,date_field=date_field).count()
        idx = idx + 1
        print idx

        if idx > cls.MAX_DAILY_TRANSFER:
            return None
        
        return "%s-%s-%s-%s-%s" % (from_mama_id, to_mama_id, template_id, date_field, idx)
    
    @classmethod
    def get_stock_num(cls, mama_id):
        from django.db.models import Sum
        res = cls.objects.filter(coupon_from_mama_id=mama_id).aggregate(n=Sum('coupon_num'))
        out_num = res['n'] or 0

        res = cls.objects.filter(coupon_to_mama_id=mama_id).aggregate(n=Sum('coupon_num'))
        in_num = res['n'] or 0

        stock_num = in_num - out_num
        return stock_num
    
    @property
    def month_day(self):
        return self.created.strftime('%m-%d')

    @property
    def hour_minute(self):
        return self.created.strftime('%H:%M')

    @property
    def transfer_status_display(self):
        return get_choice_name(self.TRANSFER_STATUS, self.transfer_status)
