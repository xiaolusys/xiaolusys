# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0004_auto_20160506_2033'),
    ]

    operations = [
        migrations.AddField(
            model_name='tmpsharecoupon',
            name='value',
            field=models.FloatField(default=0.0, verbose_name='\u4f18\u60e0\u5238\u4ef7\u503c'),
        ),
    ]
