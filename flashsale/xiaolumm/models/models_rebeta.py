# -*- encoding:utf-8 -*-
from __future__ import unicode_literals

import datetime

from django.db import models
from django.core.cache import cache
from django.db.models.signals import pre_save, post_save

from core.fields import JSONCharMyField

import logging
logger = logging.getLogger(__name__)

class AgencyOrderRebetaScheme(models.Model):
    """ 代理订单返利模板：代理等级返利设置始终生效，如果商品价格返利选上，则先查找价格返利，然后才查询代理等级返利 """
    NORMAL = 1
    CANCEL = 0
    STATUS_CHOICES = (
        (CANCEL, u'关闭'),
        (NORMAL, u'使用')
    )

    CACHE_TIME = 24 * 60 * 60
    REBETA_SCHEME_CACHE_KEY = '%s.%s'%(__name__, 'AgencyOrderRebetaScheme')

    name = models.CharField(max_length=64, blank=True, verbose_name=u'计划名称')

    agency_rebetas = JSONCharMyField(max_length=10240, blank=True,
                                     default={"1": 0},
                                     verbose_name=u'代理等级返利设置')
    price_rebetas = JSONCharMyField(max_length=10240, blank=True,
                                    default={"1": {"10": 0}},
                                    verbose_name=u'商品价格返利设置')
    price_active = models.BooleanField(default=False, verbose_name=u'根据商品价格返利')

    start_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'开始时间')
    end_time = models.DateTimeField(blank=True, null=True, db_index=True, verbose_name=u'结束时间')

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
        scheme_maps = cls.get_active_scheme_keymap()
        for scheme in scheme_maps.values():
            if scheme.is_default:
                return scheme
        return None

    @classmethod
    def get_active_scheme_keymap(cls):
        """ 缓存佣金计划 id: scheme 字典 """
        if not hasattr(cls, '_agency_rebeta_schemes_'):
            scheme_maps = cache.get(cls.REBETA_SCHEME_CACHE_KEY)
            if not scheme_maps:
                orderrebeta_qs = AgencyOrderRebetaScheme.objects.filter(status=AgencyOrderRebetaScheme.NORMAL)
                scheme_maps = dict([(rb.id, rb) for rb in orderrebeta_qs])
                cache.set(cls.REBETA_SCHEME_CACHE_KEY, scheme_maps, cls.CACHE_TIME)
            cls._agency_rebeta_schemes_ = scheme_maps
        return cls._agency_rebeta_schemes_

    @classmethod
    def get_rebeta_scheme(cls, scheme_id):
        """ 通过计划id获取佣金计划 """
        scheme_maps = cls.get_active_scheme_keymap()
        rebeta_scheme = scheme_maps.get(scheme_id)
        if rebeta_scheme:
            return rebeta_scheme
        return cls.get_default_scheme()

    def get_scheme_rebeta(self, agencylevel=None, payment=None):
        """ 根据订单支付金额，商品价格，小鹿妈妈等级，获取返利金额 """
        agency_level = '%d' % (agencylevel or 0)
        payment = payment or 0
        rebeta_rate = self.agency_rebetas.get(agency_level, 0)
        rebeta_amount = payment * rebeta_rate

        if rebeta_amount > payment:
            raise Exception(u'返利金额超过实际支付金额')

        return rebeta_amount

    def calculate_carry(self, agencylevel, product_price_yuan):
        if not self.price_active:
            return self.get_scheme_rebeta(agencylevel=agencylevel, payment=product_price_yuan)

        carry_rules = self.price_rebetas.get(str(agencylevel))
        payment = int(round(int(product_price_yuan) * 0.1) * 10)

        MAX_PAYMENT = 200
        if payment > MAX_PAYMENT:
            payment = MAX_PAYMENT

        if not carry_rules:
            return 0
        key_list = map(int, carry_rules.keys())
        key_list.sort()

        real_index = -1
        for index, key in enumerate(key_list):
            if key > payment: break
            real_index = index

        if real_index >= 0:
            calc_payment = key_list[real_index]
            return carry_rules.get(str(calc_payment))

        return 0

def invalid_agency_orderebeta_cache(sender, instance, created, **kwargs):
    logger.info('invalid_agency_orderebeta_cache：%s'% instance)
    cache_key = AgencyOrderRebetaScheme.REBETA_SCHEME_CACHE_KEY
    cache.delete(cache_key)

post_save.connect(invalid_agency_orderebeta_cache,
                  sender=AgencyOrderRebetaScheme,
                  dispatch_uid='post_save_invalid_agency_orderebeta_cache')
