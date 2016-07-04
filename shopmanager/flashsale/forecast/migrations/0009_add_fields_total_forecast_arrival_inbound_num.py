# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0008_add_has_lack_and_memo_to_forecast'),
    ]

    operations = [
        migrations.AddField(
            model_name='forecastinbound',
            name='arrival_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u5230\u8d27\u65f6\u95f4', blank=True),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='delivery_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u53d1\u8d27\u65f6\u95f4', blank=True),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='total_arrival_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u5230\u8d27\u6570'),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='total_forecast_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u9884\u6d4b\u6570'),
        ),
        migrations.AddField(
            model_name='realinbound',
            name='total_inbound_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u5165\u4ed3\u6570'),
        ),
        migrations.AddField(
            model_name='realinbound',
            name='total_inferior_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u6b21\u54c1\u6570'),
        ),
    ]
