# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class BatchNumberGroup(models.Model):
    batch_number = models.AutoField(primary_key=True, db_index=True, verbose_name=u'批号')
    group = models.CharField(max_length=100, blank=True, verbose_name=u'组')
    #    group_member = models.()
    #    created = models.DateTimeField(blank=True,null=True,verbose_name=u'创建日期')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    class Meta:
        db_table = 'batch_number_group'
        app_label = 'second_time_sort'
        verbose_name = u'批号/组'
        verbose_name_plural = u'批号/组列表'


class BatchNumberOid(models.Model):
    ACTIVE = 0
    DEACTIVE = 1
    STATUS_CHOICES = ((ACTIVE, u'未分捡'),
                      (DEACTIVE, u'分捡'),)

    batch_number = models.IntegerField(null=True, db_index=True, verbose_name=u'批号')
    out_sid = models.CharField(max_length=64, null=True, db_index=True, blank=True, verbose_name=u'物流编号', unique=True)
    #    tid     = models.BigIntegerField(null=False,db_index=True,verbose_name=u'交易ID')
    #    oid     = models.BigIntegerField(null=False,db_index=True,verbose_name=u'订单ID')
    number = models.IntegerField(null=True, db_index=True, verbose_name=u'序号')
    group = models.CharField(max_length=100, blank=True, verbose_name=u'组')
    created = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name=u'创建日期')

    status = models.IntegerField(choices=STATUS_CHOICES, default=ACTIVE, verbose_name=u"状态")

    class Meta:
        db_table = 'batch_number_oid'
        app_label = 'second_time_sort'
        verbose_name = u'批号/物流单号'
        verbose_name_plural = u'批号/物流单号'


# class BatchNumberSku(models.Model):
#    batch_number = models.AutoField(primary_key=True,db_index=True,verbose_name=u'批号')
#    outer_id = models.CharField(max_length=64,blank=True,verbose_name=u'商品外部编码')
#    outer_sku_id = models.CharField(max_length=20,blank=True,verbose_name=u'规格外部编码')
#    amount = models.IntegerField(null=True,db_index=True,verbose_name=u'数量')

class out_list_sku(models.Model):
    out_sid = models.CharField(max_length=64, null=True, db_index=True, blank=True, verbose_name=u'物流编号', unique=True)
    outer_sku_id = models.CharField(max_length=20, blank=True, verbose_name=u'规格外部编码')
    outer_id = models.CharField(max_length=64, blank=True, verbose_name=u'商品外部编码')
    amount = models.IntegerField(null=True, db_index=True, verbose_name=u'数量')

    class Meta:
        db_table = 'batch_number_oid'
        app_label = 'second_time_sort'
        verbose_name = u'批号/物流单号'
        verbose_name_plural = u'批号/物流单号'
