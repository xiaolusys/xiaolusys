# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SaleOrderStatsRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('oid', models.CharField(unique=True, max_length=40, verbose_name='sale_order_oid')),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name='\u89c4\u683c\u5916\u90e8\u7f16\u7801', blank=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u5546\u54c1SKU\u63cf\u8ff0')),
                ('pic_path', models.CharField(max_length=256, verbose_name='\u56fe\u7247')),
                ('num', models.IntegerField(default=0, verbose_name='\u6570\u91cf')),
                ('payment', models.FloatField(default=0, verbose_name='\u5b9e\u4ed8\u6b3e')),
                ('pay_time', models.DateTimeField(verbose_name='\u4ed8\u6b3e\u65f6\u95f4')),
                ('date_field', models.DateField(db_index=True, null=True, verbose_name='\u65e5\u671f', blank=True)),
                ('status', models.IntegerField(db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u4ed8\u6b3e'), (1, '\u5df2\u4ed8\u6b3e'), (2, '\u53d1\u8d27\u524d\u9000\u6b3e'), (3, '\u7f3a\u8d27\u9000\u6b3e'), (4, '\u9000\u8d27\u9000\u6b3e')])),
                ('return_goods', models.IntegerField(default=0, verbose_name='\u9000\u8d27\u6807\u8bb0', choices=[(1, '\u6709\u7533\u8bf7\u9000\u8d27'), (0, '\u65e0\u7533\u8bf7\u9000\u8d27')])),
            ],
            options={
                'db_table': 'statistics_sale_order_stats_record',
                'verbose_name': '\u4ea4\u6613\u7edf\u8ba1\u660e\u7ec6',
                'verbose_name_plural': '\u4ea4\u6613\u7edf\u8ba1\u660e\u7ec6\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SaleStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('parent_id', models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u4e0a\u4e00\u7ea7id', blank=True)),
                ('current_id', models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u7ea7\u522b\u5bf9\u5e94instance_id', blank=True)),
                ('date_field', models.DateField(verbose_name='\u4ed8\u6b3e\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=64, null=True, verbose_name='\u5546\u54c1\u63cf\u8ff0')),
                ('pic_path', models.CharField(max_length=256, null=True, verbose_name='\u56fe\u7247')),
                ('num', models.IntegerField(default=0, verbose_name='\u9500\u552e\u6570\u91cf')),
                ('payment', models.FloatField(default=0, verbose_name='\u9500\u552e\u91d1\u989d')),
                ('uni_key', models.CharField(max_length=64, verbose_name='\u552f\u4e00\u6807\u8bc6', db_index=True)),
                ('record_type', models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (10, '\u7c7b\u522b\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'), (16, '\u603b\u8ba1\u7ea7')])),
                ('status', models.IntegerField(db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u4ed8\u6b3e'), (1, '\u5df2\u4ed8\u6b3e'), (2, '\u53d1\u8d27\u524d\u9000\u6b3e'), (3, '\u7f3a\u8d27\u9000\u6b3e'), (4, '\u9000\u8d27\u9000\u6b3e')])),
            ],
            options={
                'db_table': 'statistics_sale_stats',
                'verbose_name': '\u9500\u91cf\u7edf\u8ba1\u8868',
                'verbose_name_plural': '\u9500\u91cf\u7edf\u8ba1\u5217\u8868',
            },
        ),
    ]
