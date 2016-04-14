# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DailyStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('total_click_count', models.IntegerField(default=0, verbose_name='\u65e5\u70b9\u51fb\u6570')),
                ('total_valid_count', models.IntegerField(default=0, verbose_name='\u65e5\u6709\u6548\u70b9\u51fb\u6570')),
                ('total_visiter_num', models.IntegerField(default=0, verbose_name='\u65e5\u8bbf\u5ba2\u6570')),
                ('total_new_visiter_num', models.IntegerField(default=0, verbose_name='\u65b0\u8bbf\u5ba2\u6570')),
                ('total_payment', models.IntegerField(default=0, verbose_name='\u65e5\u6210\u4ea4\u989d')),
                ('total_order_num', models.IntegerField(default=0, verbose_name='\u65e5\u8ba2\u5355\u6570')),
                ('total_buyer_num', models.IntegerField(default=0, verbose_name='\u65e5\u8d2d\u4e70\u4eba\u6570')),
                ('total_old_buyer_num', models.IntegerField(default=0, verbose_name='\u8001\u6210\u4ea4\u4eba\u6570')),
                ('total_new_order_num', models.IntegerField(default=0, verbose_name='\u65b0\u7528\u6237\u5355\u6570')),
                ('seven_buyer_num', models.IntegerField(default=0, verbose_name='\u4e03\u65e5\u8001\u6210\u4ea4\u4eba\u6570')),
                ('day_date', models.DateField(verbose_name='\u7edf\u8ba1\u65e5\u671f')),
            ],
            options={
                'db_table': 'flashsale_dailystat',
                'verbose_name': '\u7279\u5356/\u6bcf\u65e5\u7edf\u8ba1',
                'verbose_name_plural': '\u7279\u5356/\u6bcf\u65e5\u7edf\u8ba1\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='DaystatCalcResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('calc_key', models.CharField(max_length=128, verbose_name='\u8ba1\u7b97\u7ed3\u679cID', db_index=True)),
                ('calc_result', jsonfield.fields.JSONField(default={}, max_length=102400, verbose_name='\u8ba1\u7b97\u7ed3\u679cID')),
            ],
            options={
                'db_table': 'flashsale_daystat_result_cache',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\uff0f\u6570\u636e\u7edf\u8ba1\u6682\u5b58\u7ed3\u679c',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\uff0f\u6570\u636e\u7edf\u8ba1\u6682\u5b58\u7ed3\u679c',
            },
        ),
        migrations.CreateModel(
            name='PopularizeCost',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField(default=datetime.date.today, unique=True, verbose_name='\u4e1a\u52a1\u65e5\u671f', db_index=True)),
                ('carrylog_order', models.FloatField(default=0.0, verbose_name='\u8ba2\u5355\u8fd4\u5229', db_index=True)),
                ('carrylog_click', models.FloatField(default=0.0, verbose_name='\u70b9\u51fb\u8865\u8d34', db_index=True)),
                ('carrylog_thousand', models.FloatField(default=0.0, verbose_name='\u5343\u5143\u63d0\u6210', db_index=True)),
                ('carrylog_agency', models.FloatField(default=0.0, verbose_name='\u4ee3\u7406\u8865\u8d34', db_index=True)),
                ('carrylog_recruit', models.FloatField(default=0.0, verbose_name='\u62db\u52df\u5956\u91d1', db_index=True)),
                ('carrylog_order_buy', models.FloatField(default=0.0, verbose_name='\u6d88\u8d39\u652f\u51fa', db_index=True)),
                ('carrylog_cash_out', models.FloatField(default=0.0, verbose_name='\u94b1\u5305\u63d0\u73b0', db_index=True)),
                ('carrylog_deposit', models.FloatField(default=0.0, verbose_name='\u62bc\u91d1', db_index=True)),
                ('carrylog_refund_return', models.FloatField(default=0.0, verbose_name='\u9000\u6b3e\u8fd4\u73b0', db_index=True)),
                ('carrylog_red_packet', models.FloatField(default=0.0, verbose_name='\u8ba2\u5355\u7ea2\u5305')),
                ('total_carry_in', models.FloatField(default=0.0, verbose_name='\u63a8\u5e7f\u8d39\u7528', db_index=True)),
                ('total_carry_out', models.FloatField(default=0.0, verbose_name='\u5988\u5988\u652f\u51fa', db_index=True)),
            ],
            options={
                'db_table': 'flashsale_daily_popularize_cost',
                'verbose_name': '\u6bcf\u65e5\u63a8\u5e7f\u652f\u51fa',
                'verbose_name_plural': '\u6bcf\u65e5\u63a8\u5e7f\u652f\u51fa\u5217\u8868',
            },
        ),
    ]
