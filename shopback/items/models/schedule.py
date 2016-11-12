# coding: utf-8

from django.db import models
from core.models import AdminModel
from .. import constants


class ProductSchedule(AdminModel):
    r"""
    商品排期
    """
    SCHEDULE_TYPE_CHOICES = [
        (1, u'原始排期'),
        (2, u'秒杀排期')
    ]

    STATUS_CHOICES = [
        (0, u'无效'),
        (1, u'有效')
    ]

    product = models.ForeignKey('Product', related_name='schedules', verbose_name=u'关联商品')
    onshelf_datetime = models.DateTimeField(verbose_name=u'上架时间')
    onshelf_date = models.DateField(verbose_name=u'上架日期')
    onshelf_hour = models.IntegerField(verbose_name=u'上架时间')
    offshelf_datetime = models.DateTimeField(verbose_name=u'下架时间')
    offshelf_date = models.DateField(verbose_name=u'下架日期')
    offshelf_hour = models.IntegerField(verbose_name=u'下架时间')
    schedule_type = models.SmallIntegerField(choices=SCHEDULE_TYPE_CHOICES, default=1, verbose_name=u'排期类型')
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=1, verbose_name=u'状态')
    sale_type = models.SmallIntegerField(choices=constants.SALE_TYPES, default=1, verbose_name=u'促销类型')

    class Meta:
        db_table = 'shop_items_schedule'
        app_label = 'items'
        verbose_name = u'商品上下架排期管理'
        verbose_name_plural = u'商品上下架排期管理列表'
