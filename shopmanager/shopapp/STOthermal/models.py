# -*- coding:utf-8 -*-
__author__ = "huazi"

from django.db import models
from django.contrib.auth.models import User
import datetime
from .managers import STOThermalQuerySet

datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

class STOThermal(models.Model):
    waybill_code = models.CharField(max_length=32, unique=True, verbose_name=u'STO运单号')
    print_data = models.TextField(max_length=5120, verbose_name=u'热敏打印信息')
    object_id = models.CharField(max_length=32,blank=True,verbose_name="object_id")
    create_time = models.DateTimeField(default=datetime.datetime.now, verbose_name=u'创建时间')
    operation_user = models.ForeignKey(User,related_name='STO_thermal', verbose_name=u'操作人')

    objects = STOThermalQuerySet.as_manager()

    class Meta:
        db_table = 'flashsale_STOthermal'
        app_label = 'STOthermal'
        verbose_name = u'申通热敏单'
        verbose_name_plural = u'申通热敏列表'

