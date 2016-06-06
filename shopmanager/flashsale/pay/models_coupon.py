# coding=utf-8
import json
from django.db import models
from core.fields import JSONCharMyField
from .base import PayBaseModel


"""
用户  积分 模块
用户ID：SaleTrade 中的  buyer_id  也即是：models_user 中的  Customer  id '客户ID'

"""


class Integral(PayBaseModel):
    integral_user = models.BigIntegerField(null=False, unique=True, db_index=True, verbose_name=u"用户ID")
    integral_value = models.IntegerField(default=0, verbose_name=u"订单积分")

    class Meta:
        db_table = "sale_user_integral"
        app_label = 'pay'
        verbose_name = u"特卖用户/积分"
        verbose_name_plural = u"特卖用户/积分列表"

    def __unicode__(self):
        return '<%s>' % (self.id)


class IntegralLog(PayBaseModel):
    """
    记录用户积分的使用情况
    """
    CONFIRM = 1
    CANCEL = 0
    PENDING = 2
    INTEGRAL_STATUS = ((CONFIRM, u'已确定'), (CANCEL, u'已取消'), (PENDING, u'待确定'))
    ORDER_INTEGRA = 1
    LOG_TYPE = ((ORDER_INTEGRA, u'订单积分'),)
    LOG_IN = 1
    LOG_OUT = 0
    IN_OUT = ((LOG_IN, u'增加积分'), (LOG_OUT, u"减少积分"))

    integral_user = models.BigIntegerField(null=False, db_index=True, verbose_name=u"用户ID")
    order_id = models.BigIntegerField(null=False, db_index=True, verbose_name=u"订单ID")
    mobile = models.CharField(max_length=11, db_index=True, blank=True, verbose_name=u'手机')
    log_value = models.IntegerField(default=0, verbose_name=u'记录积分值')
    log_status = models.IntegerField(choices=INTEGRAL_STATUS, verbose_name=u'记录状态')
    log_type = models.IntegerField(choices=LOG_TYPE, verbose_name=u'积分类型')
    in_out = models.IntegerField(choices=IN_OUT, verbose_name=u'积分收支')
    order = JSONCharMyField(max_length=10240, blank=True,
                            default='[{"order_id":"","pic_link":"","trade_id":"","order_status":""}]',
                            verbose_name=u'订单信息')

    class Meta:
        unique_together = ('integral_user', 'order_id')
        db_table = "sale_user_integral_log"
        app_label = 'pay'
        verbose_name = u"特卖用户/积分记录表"
        verbose_name_plural = u"特卖用户/积分记录列表"

    def __unicode__(self):
        return '<%s>' % (self.id)

    @property
    def order_info(self):
        if len(self.order) == 1:
            info = json.dumps(self.order[0])
            return json.loads(info)
        else:
            return {}

