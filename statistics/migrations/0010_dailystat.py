# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0009_alter_field_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('total_stock', models.FloatField(default=0, verbose_name='\u603b\u5e93\u5b58')),
                ('total_amount', models.FloatField(default=0, verbose_name='\u603b\u91d1\u989d')),
                ('total_order', models.FloatField(default=0, verbose_name='\u6708\u8ba2\u5355\u603b\u8425\u6536')),
                ('total_purchase', models.FloatField(default=0, verbose_name='\u6708\u91c7\u8d2d\u603b\u652f\u51fa')),
                ('daytime', models.DateTimeField(verbose_name='\u7edf\u8ba1\u65e5')),
                ('note', models.CharField(max_length=1000, verbose_name='\u5907\u6ce8')),
            ],
            options={
                'db_table': 'statistics_daily_stat',
                'verbose_name': '\u5c0f\u9e7f\u65e5\u7edf\u8ba1\u8868',
                'verbose_name_plural': '\u5e93\u5b58\u7edf\u8ba1\u5217\u8868',
            },
        ),
    ]
