# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0010_unreturnsku'),
    ]

    operations = [
        migrations.AddField(
            model_name='returngoods',
            name='plan_amount',
            field=models.FloatField(default=0.0, verbose_name='\u7d22\u53d6\u9000\u6b3e\u603b\u989d'),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='real_amount',
            field=models.FloatField(default=0.0, verbose_name='\u5b9e\u9645\u9000\u6b3e\u989d'),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='sum_amount',
            field=models.FloatField(default=0.0, verbose_name='\u8ba1\u5212\u9000\u6b3e\u603b\u989d'),
        ),
    ]
