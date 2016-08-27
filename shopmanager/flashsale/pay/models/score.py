# coding=utf-8
from django.db import models
from core.fields import JSONCharMyField
from .base import PayBaseModel
from django.db.models.signals import post_save


class Integral(PayBaseModel):
    integral_user = models.BigIntegerField(null=False, unique=True, verbose_name=u"用户ID")
    integral_value = models.IntegerField(default=0, verbose_name=u"订单积分")

    class Meta:
        db_table = "sale_user_integral"
        app_label = 'pay'
        verbose_name = u"特卖用户/积分"
        verbose_name_plural = u"特卖用户/积分列表"

    def __unicode__(self):
        return '<%s-%s>' % (self.id, self.integral_user)

    @classmethod
    def create_integral(cls, customer_id, integral_value=0):
        integral = cls(integral_user=customer_id, integral_value=integral_value)
        integral.save()
        return integral

    def update_integral_value(self, integral_value):
        """ update the total point """
        if self.integral_value != integral_value:
            self.integral_value = integral_value
            self.save(update_fields=['integral_value'])
            return True
        return False


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
    order = JSONCharMyField(max_length=10240, blank=True, default={}, verbose_name=u'订单信息')

    class Meta:
        unique_together = ('integral_user', 'order_id')
        db_table = "sale_user_integral_log"
        app_label = 'pay'
        verbose_name = u"特卖用户/积分记录表"
        verbose_name_plural = u"特卖用户/积分记录列表"

    def __unicode__(self):
        return '<%s-%s>' % (self.id, self.order_id)


def calculate_total_order_integral(sender, instance, created, **kwargs):
    from flashsale.pay.tasks import task_calculate_total_order_integral
    # 计算总积分到用户积分

    task_calculate_total_order_integral.delay(instance)


post_save.connect(calculate_total_order_integral, sender=IntegralLog,
                  dispatch_uid='post_save_calculate_total_order_integral')
