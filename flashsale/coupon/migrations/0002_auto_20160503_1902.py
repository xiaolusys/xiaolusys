# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0001_initialb'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercoupon',
            name='order_coupon_id',
            field=models.IntegerField(db_index=True, null=True, verbose_name='\u8ba2\u5355\u4f18\u60e0\u5238\u5206\u4eabID', blank=True),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='share_user_id',
            field=models.IntegerField(db_index=True, null=True, verbose_name='\u5206\u4eab\u7528\u6237ID', blank=True),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='trade_tid',
            field=models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u7ed1\u5b9a\u4ea4\u6613tid', blank=True),
        ),
    ]
