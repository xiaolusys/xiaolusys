# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0015_dailystat_add_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='XlmmDailyStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('total', models.IntegerField(default=0, verbose_name='\u5988\u5988\u603b\u6570')),
                ('new_join', models.IntegerField(default=0, verbose_name='\u65b0\u52a0\u5165\u5988\u5988\u603b\u6570')),
                ('new_pay', models.IntegerField(default=0, verbose_name='\u65b0\u4ed8\u6b3e\u5988\u5988\u603b\u6570')),
                ('new_activite', models.IntegerField(default=0, verbose_name='\u65b0\u6fc0\u6d3b\u5988\u5988\u603b\u6570')),
                ('new_hasale', models.IntegerField(default=0, verbose_name='\u65b0\u51fa\u8d27\u5988\u5988\u603b\u6570')),
                ('new_trial', models.IntegerField(default=0, verbose_name='\u65b0\u52a0\u5165\u4e00\u5143\u5988\u5988\u603b\u6570')),
                ('new_trial_activite', models.IntegerField(default=0, verbose_name='\u65b0\u6fc0\u6d3b\u4e00\u5143\u5988\u5988\u603b\u6570')),
                ('new_trial_hasale', models.IntegerField(default=0, verbose_name='\u65b0\u51fa\u8d27\u4e00\u5143\u5988\u5988\u603b\u6570')),
                ('new_task', models.IntegerField(default=0, verbose_name='\u65b0\u505a\u4efb\u52a1\u4e00\u603b\u6570')),
                ('new_lesson', models.IntegerField(default=0, verbose_name='\u65b0\u4e0a\u8bfe\u603b\u6570')),
                ('new_award', models.IntegerField(default=0, verbose_name='\u65b0\u5956\u52b1\u603b\u6570')),
                ('date_field', models.DateField(unique=True, verbose_name='\u65e5\u671f')),
            ],
            options={
                'db_table': 'statistics_xlmm_daily_stat',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u65e5\u7edf\u8ba1\u8868',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u65e5\u7edf\u8ba1\u8868',
            },
        ),
    ]
