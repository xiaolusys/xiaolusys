# -*- encoding:utf-8 -*-
from django.db import models
from core.fields import JSONCharMyField


class AgencyOrderRebetaScheme(models.Model):
    """ 代理订单返利模板：代理等级返利设置始终生效，如果商品价格返利选上，则先查找价格返利，然后才查询代理等级返利 """
    NORMAL = 1
    CANCEL = 0
    STATUS_CHOICES = (
        (CANCEL, u'关闭'),
        (NORMAL, u'使用')
    )
    name = models.CharField(max_length=64, blank=True, verbose_name=u'计划名称')

    agency_rebetas = JSONCharMyField(max_length=10240, blank=True,
                                     default=lambda: {"1": [0, 0]},
                                     verbose_name=u'代理等级返利设置')
    price_rebetas = JSONCharMyField(max_length=10240, blank=True,
                                    default=lambda: [{"100": {"1": [0, 0]}}],
                                    verbose_name=u'商品价格返利设置')
    price_active = models.BooleanField(default=False, verbose_name=u'价格返利生效')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    modified = models.DateTimeField(auto_now=True, db_index=True, verbose_name=u'修改时间')

    is_default = models.BooleanField(default=False, verbose_name=u'默认设置')
    status = models.IntegerField(choices=STATUS_CHOICES, default=NORMAL, verbose_name=u'状态')

    class Meta:
        db_table = 'xiaolumm_productrebeta'
        app_label = 'xiaolumm'
        verbose_name = u'妈妈订单返利计划'
        verbose_name_plural = u'妈妈订单返利计划'

    def __unicode__(self):
        return u'<%d,%s>' % (self.id, self.name)

    @classmethod
    def get_default_scheme(cls):
        qs = cls.objects.filter(status=cls.NORMAL, is_default=True)
        if qs.exists():
            return qs[0]
        return None

    def get_scheme_rebeta(self, **kwargs):
        """ 根据订单支付金额，商品价格，小鹿妈妈等级，获取返利金额 """
        agency_level = '%d' % kwargs.get('agencylevel', 0)
        payment = kwargs.get('payment', 0)
        rebeta_rate = self.agency_rebetas.get(agency_level, [0, 0])
        rebeta_amount = 0
        if rebeta_rate[0] > 0:
            rebeta_amount = payment * rebeta_rate[0]
        else:
            rebeta_amount = max(rebeta_rate[1] * 100, 0)

        if rebeta_amount > payment:
            raise Exception('返利金额超过实际支付')

        return rebeta_amount

    def calculate_carry(self, agencylevel, payment):
        carry_rules = self.price_rebetas.get(str(agencylevel))
        payment = int(round(int(payment) * 0.1) * 10)

        MAX_PAYMENT = 200
        if payment > MAX_PAYMENT:
            payment = MAX_PAYMENT

        key = str(payment)
        if key in carry_rules:
            carry = carry_rules[key]
            return carry

        return 0


def calculate_price_carry(agencylevel, payment_yuan, policy):
    """
    payment_yuan: payment in YUAN
    policy: whole carry policy (a dict)

    return carry in YUAN.
    """

    carry_rules = policy.get(str(agencylevel))

    if not carry_rules:
        return 0

    payment = int(round(int(payment_yuan) * 0.1) * 10)

    MAX_PAYMENT = 200  # YUAN
    if payment > MAX_PAYMENT:
        payment = MAX_PAYMENT

    key = str(payment)
    if key in carry_rules:
        carry = carry_rules[key]
        return carry

    return 0
