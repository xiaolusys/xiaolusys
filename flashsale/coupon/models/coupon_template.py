# coding=utf-8
import random
import datetime
from core.models import BaseModel
from django.db import models

from core.utils.unikey import uniqid
from core.fields import JSONCharMyField
from .managers.coupon_template import UserCouponTemplateManager


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

def default_coupon_template_no(date=None):
    dt = date or datetime.date.today()
    return uniqid('%s%s' % (CouponTemplate.PREFIX_NO, dt.strftime('%y%m%d')))

class CouponTemplate(BaseModel):
    """ 优惠券模板 """

    PREFIX_NO = 'tcp'

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
    SCOPE_TYPES = ((SCOPE_OVERALL, u"特卖商品通用"),
                   (SCOPE_CATEGORY, u"类目专用"),
                   (SCOPE_PRODUCT, u"商品专用"))

    CREATE = 0
    SENDING = 1
    FINISHED = 2
    CANCEL = 3
    STATUS_CHOICES = (
        (CREATE, u'未发放'),  # 定义模板后没有发放 待用
        (SENDING, u'发放中'),  # 模板正在使用中
        (FINISHED, u'已结束'),  # 正常发放后结束发放
        (CANCEL, u'已取消'),
    )  # 发放中到取消状态取消发放

    template_no = models.CharField(max_length=64, unique=True,
                                   default=default_coupon_template_no, verbose_name=u"优惠券no")  # type: text_type

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
    objects = UserCouponTemplateManager()

    class Meta:
        db_table = "flashsale_coupon_template"
        app_label = 'coupon'
        verbose_name = u"特卖/优惠券/模板"
        verbose_name_plural = u"特卖/优惠券/模板列表"

    def __unicode__(self):
        # type: () -> text_type
        return '<%s,%s>' % (self.id, self.title)

    @classmethod
    def gen_default_template_no(cls, date=None):
        return default_coupon_template_no(date=date)

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

    @classmethod
    def get_product_img(cls, template_id):
        t = cls.objects.filter(id=template_id).first()
        if t:
            return t.extras.get("product_img") or ''
        return ''

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

        # 商品只能使用指定优惠券
        for mp in model_products:
            use_coupon_only = mp.extras.get('payinfo', {}).get('use_coupon_only', False)
            if not use_coupon_only:
                continue
            coupon_template_ids = mp.extras.get('payinfo', {}).get('coupon_template_ids', [])
            if self.id not in coupon_template_ids:
                raise AssertionError(u'该商品不能使用这个优惠券')

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

    def make_uniq_id(self, customer_id, trade_id=None, share_id=None, cashout_id=None, count=0):
        # type: (int, Optional[int], Optional[int], Optional[int], Optional[int]) -> text_type
        """生成uni_key
        """
        uniqs = [self.id, self.coupon_type, customer_id]
        if trade_id:
            uniqs.append(trade_id)
        elif share_id:
            uniqs.append(share_id)
        elif self.coupon_type == CouponTemplate.TYPE_CASHOUT_EXCHANGE and cashout_id:  # 优惠券兑换　7
            uniqs.append(cashout_id)
        elif count:
            uniqs.append(count)
        return '_'.join([str(i) for i in uniqs])

    def gen_usercoupon_unikey(self, order_id, index=0):
        # type: (int, int) -> text_type
        """生成对应优惠券的unique key
        """
        return "%s_%s_%s_%s" % (self.id, self.coupon_type, order_id, index)

    def calculate_value(self):
        # type: () -> float
        """计算优惠券价值(支持比例配置:配置格式如下)
          "randoms": {
            "zone_config": {
              "zone": [[3, 5],[5, 8]]
              "zone_rate": [10, 1],
            },
            "max_val": 8,
            "min_val": 5
          },
        """
        value = self.value  # 默认取模板默认值
        if self.is_random_val and self.min_val and self.max_val:  # 如果设置了随机值则选取随机值
            value = float('%.1f' % random.uniform(self.max_val, self.min_val))  # 生成随机的value
            randoms = self.extras.get('randoms')
            if randoms:
                zone_config = randoms.get('zone_config')
                if zone_config:
                    zone_rate = zone_config.get('zone_rate')
                    zone = zone_config.get('zone')
                    choice_l = []
                    for index, v in enumerate(zone_rate):
                        for i in range(v):
                            choice_l.append(index)
                    target = random.choice(choice_l)
                    target_zone = zone[target]
                    value = float('%.1f' % random.uniform(target_zone[0], target_zone[1]))
        return value

    def calculate_value_and_time(self):
        # type: (CouponTemplate) -> Tuple[float, datetime.datetime, datetime.datetime]
        """计算发放优惠券价值和开始使用时间和结束时间
        """
        value = self.calculate_value()
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

