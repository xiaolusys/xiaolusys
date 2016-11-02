# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0002_auto_20160422_1510'),
    ]

    operations = [
        # migrations.AddField(
        #     model_name='packageorder',
        #     name='sku_num',
        #     field=models.IntegerField(default=0, verbose_name='SKU\u79cd\u7c7b\u6570'),
        # ),
        migrations.AddField(
            model_name='packageskuitem',
            name='oid',
            field=models.CharField(max_length=40, null=True, verbose_name='\u539f\u5355ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='mergeorder',
            name='outer_id',
            field=models.CharField(max_length=32, verbose_name='\u5546\u54c1\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='mergeorder',
            name='outer_sku_id',
            field=models.CharField(max_length=32, verbose_name='\u89c4\u683c\u7f16\u7801', blank=True),
        ),
    ]
