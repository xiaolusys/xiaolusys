# -*- coding:utf-8 -*-
__author__ = 'yan.huang'
from django.db import models
import datetime


class Complain(models.Model):
    SALE_PRO = 0
    ORDER_PRO = 1
    SUGGEST = 2
    SALE_AFTER = 4
    OTHER = 3
    TYPE_CHOICES = ((SALE_PRO, U'未分类'),
                    (ORDER_PRO, U'订单/配送'),
                    (SALE_AFTER, U'售后问题'),
                    (SUGGEST, U'产品建议'),
                    (OTHER, U'其他问题'),)
    com_type = models.IntegerField(choices=TYPE_CHOICES, default=OTHER, verbose_name=u'类型')
    user_id = models.CharField(max_length=32, db_index=True, blank=True, verbose_name=u'投诉人ID')
    com_title = models.CharField(max_length=64, db_index=True, blank=True, default=u'问题反馈', verbose_name=u'标题')
    com_content = models.TextField(max_length=1024, blank=True, verbose_name=u'内容')
    contact_way = models.CharField(max_length=128, blank=True, verbose_name=u'联系方式')
    created_time = models.DateField(verbose_name=u'投诉时间', auto_now_add=True, null=True, blank=True)
    CREATED = 0
    REPLIED = 1
    CLOSED = 2
    INVALID = 3
    STATUS_CHOICES = ((CREATED, U'未处理'),
                      (REPLIED, U'已回复'),
                      (CLOSED, U'已关闭'),
                      (INVALID, U'已删除'),)
    status = models.IntegerField(choices=STATUS_CHOICES, default=CREATED, verbose_name=u'状态')
    custom_serviced = models.CharField(max_length=32, blank=True, verbose_name=u'客服号')
    reply = models.CharField(max_length=1024, blank=True, verbose_name=u'回复')
    reply_time = models.DateTimeField(null=True, blank=True, verbose_name=u'回复时间')

    class Meta:
        ordering = ('created_time', 'user_id',)
        db_table = 'complain'
        verbose_name = u'问题反馈'
        verbose_name_plural = u'投诉建议表'

    def __unicode__(self):
        return u"%s,%s" % (self.id, self.com_title)

    def respond(self, custom_serviced_name, reply):
        self.custom_serviced = custom_serviced_name
        self.reply = reply
        self.status = Complain.REPLIED
        self.reply_time = datetime.datetime.now()
        return self.save()

    def close(self, custom_serviced_name):
        self.reply_time = datetime.datetime.now()
        self.custom_serviced = custom_serviced_name
        self.status = Complain.CLOSED
        self.save()