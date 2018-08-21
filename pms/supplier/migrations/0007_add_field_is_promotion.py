# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0006_saleproduct_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproductmanagedetail',
            name='is_promotion',
            field=models.BooleanField(default=False, verbose_name='\u63a8\u5e7f\u5546\u54c1'),
        ),
        migrations.AlterField(
            model_name='saleproduct',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
        ),
        migrations.AlterField(
            model_name='saleproduct',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
        ),
    ]
