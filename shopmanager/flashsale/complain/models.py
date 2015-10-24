# -*- coding:utf-8 -*-
__author__ = 'timi06'
from django.db import models


class Complain(models.Model):

    WAIT_AUDIT = 0
    WAIT_DELIVERY = 1
    RECEIVER_CONFIRM = 2
    INVALID = 3

    STATUS_CHOICES = ((WAIT_AUDIT, U'未处理'),
                      (WAIT_DELIVERY, U'已处理'),
                      (RECEIVER_CONFIRM, U'已作废'),
                      (INVALID, U'已删除'),)

    YI = 0
    ER = 1
    SAN = 2
    SI = 3

    TYPE_CHOICES = ((YI, U'购物问题'),
                      (ER, U'订单相关'),
                      (SAN, U'意见/建议'),
                      (SI, U'其他'),)

    com_type = models.IntegerField(choices=TYPE_CHOICES, default=SI, verbose_name=u'类型')
    insider_phone = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'投诉人ID')
    com_title = models.CharField(max_length=64, db_index=True, blank=True, default=u'问题反馈', verbose_name=u'标题')
    com_content = models.TextField(max_length=1024, blank=True, verbose_name=u'内容')
    contact_way = models.CharField(max_length=128, blank=True, verbose_name=u'联系方式')
    created_time = models.DateField(verbose_name=u'投诉时间', auto_now_add=True, null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES, default=WAIT_AUDIT, verbose_name=u'状态')
    custom_serviced = models.CharField(max_length=32, blank=True, verbose_name=u'客服号')
    reply = models.CharField(max_length=1024, blank=True, verbose_name=u'回复')
    reply_time = models.DateTimeField(null=True, blank=True, verbose_name=u'回复时间')



    class Meta:
        ordering = ('created_time', 'insider_phone',)
        db_table = 'complain'
        verbose_name = u'问题反馈'
        verbose_name_plural = u'投诉建议表'

    def __unicode__(self):
        return self.com_title
