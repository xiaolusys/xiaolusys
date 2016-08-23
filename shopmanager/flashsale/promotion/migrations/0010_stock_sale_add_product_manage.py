# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0027_add_qqweixin_suppliername_index'),
        ('promotion', '0009_auto_20160723_2108'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitystocksale',
            name='product_manage',
            field=models.ForeignKey(verbose_name='\u4e13\u9898\u6d3b\u52a8', blank=True, to='supplier.SaleProductManage', null=True),
        )
    ]
