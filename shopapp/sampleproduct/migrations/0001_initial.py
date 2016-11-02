# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SampleProduct',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outer_id', models.CharField(db_index=True, max_length=16, verbose_name='\u5546\u54c1\u7f16\u7801', blank=True)),
                ('title', models.CharField(db_index=True, max_length=64, verbose_name='\u5546\u54c1\u540d\u79f0', blank=True)),
                ('supplier', models.CharField(max_length=64, verbose_name='\u4f9b\u5e94\u5546', blank=True)),
                ('pic_path', models.CharField(max_length=256, verbose_name='\u56fe\u7247\u94fe\u63a5', blank=True)),
                ('buyer', models.CharField(default=b'', max_length=32, verbose_name='\u91c7\u8d2d\u5458', blank=True)),
                ('num', models.IntegerField(default=0, verbose_name='\u6837\u54c1\u603b\u5e93\u5b58\u6570\u91cf')),
                ('payment', models.FloatField(default=0, verbose_name='\u4ed8\u6b3e\u91d1\u989d')),
                ('status', models.IntegerField(default=0, verbose_name='\u6837\u54c1\u72b6\u6001', choices=[(0, '\u5df2\u63d0\u4ea4'), (1, '\u5df2\u5ba1\u6838'), (2, '\u5df2\u626b\u63cf'), (3, '\u5df2\u4f5c\u5e9f')])),
            ],
            options={
                'db_table': 'sample_product',
                'verbose_name': '\u6837\u54c1',
                'verbose_name_plural': '\u6837\u54c1\u4fe1\u606f\u8868',
            },
        ),
        migrations.CreateModel(
            name='SampleProductSku',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('outer_id', models.CharField(db_index=True, max_length=16, verbose_name='\u89c4\u683c\u7f16\u7801', blank=True)),
                ('sku_name', models.CharField(max_length=64, verbose_name='\u89c4\u683c\u5c3a\u5bf8', blank=True)),
                ('cost', models.FloatField(default=0, verbose_name='\u91c7\u8d2d\u4ef7\u683c')),
                ('payable', models.FloatField(default=0, verbose_name='\u5e94\u4ed8\u91d1\u989d')),
                ('std_price', models.FloatField(default=0, verbose_name='\u540a\u724c\u4ef7')),
                ('num', models.IntegerField(default=0, verbose_name='\u89c4\u683c\u5e93\u5b58\u6570\u91cf')),
                ('purchase_num', models.IntegerField(default=0, verbose_name='\u91c7\u8d2d\u6570\u91cf')),
                ('storage_num', models.IntegerField(default=0, verbose_name='\u626b\u63cf\u6570\u91cf')),
                ('sell_num', models.IntegerField(default=0, verbose_name='\u51fa\u552e\u6570\u91cf')),
                ('status', models.IntegerField(default=0, verbose_name='\u89c4\u683c\u72b6\u6001', choices=[(0, '\u6b63\u5e38'), (1, '\u4f5c\u5e9f')])),
                ('product', models.ForeignKey(verbose_name='\u6240\u5c5e\u6837\u54c1', to='sampleproduct.SampleProduct')),
            ],
            options={
                'db_table': 'sample_product_sku',
                'verbose_name': '\u6837\u54c1\u89c4\u683c',
            },
        ),
        migrations.CreateModel(
            name='SampleScan',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pid', models.IntegerField(verbose_name='\u5546\u54c1ID', db_index=True)),
                ('sku_id', models.IntegerField(verbose_name='\u89c4\u683cID', db_index=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u540d\u79f0', blank=True)),
                ('sku_name', models.CharField(max_length=64, verbose_name='\u89c4\u683c\u540d\u79f0', blank=True)),
                ('bar_code', models.CharField(max_length=64, verbose_name='\u626b\u63cf\u6761\u7801', blank=True)),
                ('scan_num', models.IntegerField(default=0, verbose_name='\u626b\u63cf\u6570\u91cf')),
                ('scan_type', models.CharField(max_length=8, verbose_name='\u626b\u63cf\u7c7b\u578b', choices=[(b'in', '\u626b\u63cf\u5165\u5e93'), (b'out', '\u626b\u63cf\u51fa\u5e93')])),
                ('created', models.DateField(auto_now_add=True, verbose_name='\u626b\u63cf\u65f6\u95f4', null=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u5904\u7406\u72b6\u6001', choices=[(0, '\u672a\u786e\u8ba4'), (1, '\u5df2\u786e\u8ba4'), (2, '\u4f5c\u5e9f')])),
            ],
            options={
                'db_table': 'sample_scan',
                'verbose_name': '\uff08\u51fa\uff09\u5165\u5e93\u8868',
                'verbose_name_plural': '\u6837\u54c1\uff08\u51fa\uff09\u5165\u5e93\u8bb0\u5f55\u8868',
            },
        ),
        migrations.CreateModel(
            name='ScanLinShi',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pid', models.IntegerField(verbose_name='\u5546\u54c1ID', db_index=True)),
                ('sku_id', models.IntegerField(verbose_name='\u89c4\u683cID', db_index=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u540d\u79f0', blank=True)),
                ('sku_name', models.CharField(max_length=64, verbose_name='\u89c4\u683c\u540d\u79f0', blank=True)),
                ('bar_code', models.CharField(max_length=64, verbose_name='\u626b\u63cf\u6761\u7801', blank=True)),
                ('scan_num', models.IntegerField(default=0, verbose_name='\u626b\u63cf\u6570\u91cf')),
                ('scan_type', models.IntegerField(verbose_name='\u626b\u63cf\u7c7b\u578b')),
                ('status', models.IntegerField(default=0, verbose_name='\u5904\u7406\u72b6\u6001')),
            ],
            options={
                'db_table': 'scan_linshi',
                'verbose_name': '\u4e34\u65f6\u8868',
                'verbose_name_plural': '\u626b\u63cf\u4e34\u65f6\u8868',
            },
        ),
    ]
