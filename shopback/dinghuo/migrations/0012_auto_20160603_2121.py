# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0011_auto_20160602_1958'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='completed_time',
            field=models.DateTimeField(null=True, verbose_name='\u5b8c\u6210\u65f6\u95f4', blank=True),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='plan_amount',
            field=models.FloatField(default=0.0, verbose_name='\u8ba1\u5212\u9000\u6b3e\u603b\u989d'),
        ),
    ]
