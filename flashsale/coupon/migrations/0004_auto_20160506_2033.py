# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0003_auto_20160506_1720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tmpsharecoupon',
            name='share_coupon_id',
            field=models.CharField(max_length=32, verbose_name='\u5206\u4eabuniq_id', db_index=True),
        ),
    ]
