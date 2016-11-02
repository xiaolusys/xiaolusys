# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.pay.models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='couponspool',
            name='coupon_no',
            field=models.CharField(default=flashsale.pay.models.default_coupon_no, unique=True, max_length=32, verbose_name='\u4f18\u60e0\u5238\u53f7\u7801', db_index=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='nick',
            field=models.CharField(default=flashsale.pay.models.genCustomerNickname, max_length=32, verbose_name='\u6635\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='oid',
            field=models.CharField(default=flashsale.pay.models.default_oid, unique=True, max_length=40, verbose_name='\u539f\u5355ID'),
        ),
    ]
