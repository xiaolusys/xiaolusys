# coding=utf-8
from __future__ import unicode_literals
from django.db import models


BuyerGroupNo = ((0, u'未分组'), (1, u'A组'), (2, u'B组'), (3, u'C组'))


class BuyerGroup(models.Model):
    buyer_name = models.CharField(max_length=32, null=True, blank=True, verbose_name=u'买手姓名')
    buyer_group = models.IntegerField(default=0, choices=BuyerGroupNo, blank=True, verbose_name=u'买手分组')
    created = models.DateTimeField(null=True, blank=True, auto_now=True, verbose_name=u'创建日期')
    modified = models.DateTimeField(null=True, blank=True, auto_now_add=True, verbose_name=u'修改日期')

    class Meta:
        db_table = 'supply_chain_buyer_group'
        app_label = 'supplier'
        verbose_name = u'买手分组'
        verbose_name_plural = u'买手分组列表'