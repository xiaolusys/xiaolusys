# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0010_auto_20160511_2328'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='logistics_company_name',
            field=models.CharField(max_length=16, verbose_name='\u7269\u6d41\u516c\u53f8', blank=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='out_sid',
            field=models.CharField(max_length=64, verbose_name='\u7269\u6d41\u7f16\u53f7', blank=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='receiver_mobile',
            field=models.CharField(db_index=True, max_length=11, verbose_name='\u6536\u8d27\u624b\u673a', blank=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='sale_trade_id',
            field=models.CharField(max_length=40, null=True, verbose_name='\u4ea4\u6613\u5355\u53f7', db_index=True),
        ),
    ]
