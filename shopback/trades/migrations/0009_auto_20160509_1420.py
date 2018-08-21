# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0008_packageskuitem_package_order_pid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packageorder',
            name='id',
            field=models.CharField(unique=True, max_length=100, verbose_name='\u5305\u88f9\u7801'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='pid',
            field=models.AutoField(serialize=False, verbose_name='\u5305\u88f9\u5355\u53f7', primary_key=True),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='tid',
            field=models.CharField(max_length=32, verbose_name='\u53c2\u8003\u4ea4\u6613\u5355\u53f7'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='oid',
            field=models.CharField(max_length=40, null=True, verbose_name='SKU\u4ea4\u6613\u5355\u53f7', db_index=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='package_order_pid',
            field=models.IntegerField(null=True, verbose_name='\u5305\u88f9\u5355\u53f7', db_index=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='sale_order_id',
            field=models.IntegerField(unique=True, verbose_name='SKU\u8ba2\u5355\u7f16\u7801'),
        ),
    ]
