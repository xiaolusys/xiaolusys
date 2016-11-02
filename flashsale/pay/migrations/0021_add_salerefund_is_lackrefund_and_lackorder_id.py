# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0020_add_field_act_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerefund',
            name='is_lackrefund',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u7f3a\u8d27\u81ea\u52a8\u9000\u6b3e'),
        ),
        migrations.AddField(
            model_name='salerefund',
            name='lackorder_id',
            field=models.IntegerField(null=True, verbose_name='\u7f3a\u8d27\u5355ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='item_id',
            field=models.CharField(db_index=True, max_length=64, verbose_name='\u5546\u54c1ID', blank=True),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='sku_id',
            field=models.CharField(db_index=True, max_length=20, verbose_name='\u5c5e\u6027\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='saleordersynclog',
            name='type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u7c7b\u578b', choices=[(0, '\u672a\u77e5'), (1, '\u53d1\u8d27PSI'), (2, '\u8ba2\u8d27PR'), (3, '\u8ba2\u8d27NUM'), (7, '\u5305\u88f9SKU\u5b8c\u6210\u8ba1\u6570'), (5, '\u5165\u5e93\u6709\u591a\u8d27'), (6, '\u5165\u5e93\u6709\u6b21\u54c1'), (4, '\u5305\u88f9SKU\u5b9e\u65f6\u8ba1\u6570'), (8, '\u5907\u8d27\u8ba1\u6570'), (9, '\u6709\u5e93\u5b58\u672a\u5907\u8d27'), (10, '\u8d2d\u7269\u8f66\u8ba2\u5355\u6570'), (11, '\u5f85\u652f\u4ed8\u8ba2\u5355\u6570')]),
        ),
    ]
