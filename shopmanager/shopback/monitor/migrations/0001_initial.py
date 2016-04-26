# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DayMonitorStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=64)),
                ('year', models.IntegerField()),
                ('month', models.IntegerField()),
                ('day', models.IntegerField()),
                ('update_trade_increment', models.BooleanField(default=False)),
                ('update_purchase_increment', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'shop_monitor_daymonitortatus',
                'verbose_name': '\u5e97\u94fa\u66f4\u65b0\u72b6\u6001',
                'verbose_name_plural': '\u5e97\u94fa\u66f4\u65b0\u72b6\u6001\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Reason',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('reason_text', models.TextField(max_length=64, verbose_name=b'\xe9\x97\xae\xe9\xa2\x98\xe5\x8e\x9f\xe5\x9b\xa0')),
                ('priority', models.IntegerField(default=0, verbose_name=b'\xe4\xbc\x98\xe5\x85\x88\xe7\xba\xa7')),
                ('created', models.DateTimeField(auto_now=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f')),
            ],
            options={
                'db_table': 'shop_monitor_reason',
                'verbose_name': '\u8ba2\u5355\u95ee\u9898',
                'verbose_name_plural': '\u8ba2\u5355\u95ee\u9898\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SystemConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_rule_auto', models.BooleanField(default=False, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe5\x8c\xb9\xe9\x85\x8d')),
                ('is_sms_auto', models.BooleanField(default=False, verbose_name=b'\xe7\x9f\xad\xe4\xbf\xa1\xe6\x8f\x90\xe9\x86\x92')),
                ('is_flag_auto', models.BooleanField(default=False, verbose_name=b'\xe5\x90\x8c\xe6\xad\xa5\xe6\x97\x97\xe5\xb8\x9c')),
                ('storage_num_to_stock_auto', models.BooleanField(default=False, verbose_name=b'\xe7\xa1\xae\xe8\xae\xa4\xe5\x85\xa5\xe5\xba\x93\xe6\x95\xb0\xe8\x87\xaa\xe5\x8a\xa8\xe5\x85\xa5\xe5\xba\x93\xe5\xad\x98')),
                ('purchase_price_to_cost_auto', models.BooleanField(default=False, verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe8\xbf\x9b\xe4\xbb\xb7\xe8\x87\xaa\xe5\x8a\xa8\xe5\x90\x8c\xe6\xad\xa5\xe6\x88\x90\xe6\x9c\xac')),
                ('normal_print_limit', models.BooleanField(default=True, verbose_name=b'\xe5\x8d\x95\xe6\x89\x93\xe6\xa8\xa1\xe5\xbc\x8f\xe8\xbf\x9e\xe6\x89\x93')),
                ('per_request_num', models.IntegerField(default=30, verbose_name=b'\xe6\x9c\x80\xe5\xa4\xa7\xe5\x8d\x95\xe6\xac\xa1\xe9\x94\x81\xe5\xae\x9a\xe5\x8d\x95\xe6\x95\xb0')),
                ('client_num', models.IntegerField(default=1, verbose_name=b'\xe5\xae\xa2\xe6\x88\xb7\xe7\xab\xaf\xe6\x95\xb0\xe9\x87\x8f')),
                ('jhs_logistic_code', models.CharField(max_length=20, null=True, verbose_name=b'\xe8\x81\x9a\xe5\x88\x92\xe7\xae\x97\xe6\x8c\x87\xe5\xae\x9a\xe5\xbf\xab\xe9\x80\x92', blank=True)),
                ('category_updated', models.DateTimeField(null=True, verbose_name=b'\xe7\xb1\xbb\xe7\x9b\xae\xe6\x9b\xb4\xe6\x96\xb0\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('mall_order_updated', models.DateTimeField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x9f\x8e\xe8\xae\xa2\xe5\x8d\x95\xe6\x9b\xb4\xe6\x96\xb0\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('fenxiao_order_updated', models.DateTimeField(null=True, verbose_name=b'\xe5\x88\x86\xe9\x94\x80\xe8\xae\xa2\xe5\x8d\x95\xe6\x9b\xb4\xe6\x96\xb0\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
            ],
            options={
                'db_table': 'shop_monitor_systemconfig',
                'verbose_name': '\u7cfb\u7edf\u8bbe\u7f6e',
                'verbose_name_plural': '\u7cfb\u7edf\u8bbe\u7f6e',
            },
        ),
        migrations.CreateModel(
            name='TradeExtraInfo',
            fields=[
                ('tid', models.BigIntegerField(serialize=False, primary_key=True)),
                ('is_update_amount', models.BooleanField(default=False)),
                ('is_update_logistic', models.BooleanField(default=False)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'shop_monitor_tradeextrainfo',
                'verbose_name': '\u4ea4\u6613\u66f4\u65b0\u72b6\u6001',
                'verbose_name_plural': '\u4ea4\u6613\u66f4\u65b0\u72b6\u6001',
            },
        ),
        migrations.AlterUniqueTogether(
            name='daymonitorstatus',
            unique_together=set([('user_id', 'year', 'month', 'day')]),
        ),
    ]
