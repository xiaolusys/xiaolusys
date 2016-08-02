# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0025_xlmm_add_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='xiaolumama',
            name='active',
            field=models.BooleanField(default=False, help_text='\u6709\u83b7\u5f97\u6536\u76ca', verbose_name='\u5df2\u6fc0\u6d3b'),
        ),
        migrations.AddField(
            model_name='xiaolumama',
            name='active_time',
            field=models.DateTimeField(null=True, verbose_name='\u6fc0\u6d3b\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='xiaolumama',
            name='hasale_time',
            field=models.DateTimeField(null=True, verbose_name='\u6709\u8d2d\u4e70\u65f6\u95f4'),
        )
    ]
