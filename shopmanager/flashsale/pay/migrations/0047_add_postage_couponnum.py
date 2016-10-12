# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0046_activityproduct_jump_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerefund',
            name='coupon_num',
            field=models.IntegerField(default=0, verbose_name='\u4f18\u60e0\u5238\u91d1\u989d(\u5206)'),
        ),
        migrations.AddField(
            model_name='salerefund',
            name='postage_num',
            field=models.IntegerField(default=0, verbose_name='\u9000\u90ae\u8d39\u91d1\u989d(\u5206)'),
        )
    ]
