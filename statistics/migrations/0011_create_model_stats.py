# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0010_dailystat'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('model_id', models.BigIntegerField(verbose_name='\u6b3e\u5f0fid', db_index=True)),
                ('sale_product', models.BigIntegerField(verbose_name='\u9009\u54c1id', db_index=True)),
                ('upshelf_time', models.DateTimeField(verbose_name='\u4e0a\u67b6\u65f6\u95f4', db_index=True)),
                ('offshelf_time', models.DateTimeField(verbose_name='\u4e0b\u67b6\u65f6\u95f4', db_index=True)),
                ('category', models.CharField(max_length=64, verbose_name='\u4ea7\u54c1\u7c7b\u522b', db_index=True)),
                ('supplier', models.IntegerField(verbose_name='\u4f9b\u5e94\u5546', db_index=True)),
                ('category_name', models.CharField(max_length=64, verbose_name='\u4ea7\u54c1\u7c7b\u522b\u540d\u79f0')),
                ('pic_url', models.CharField(max_length=512, verbose_name='\u5546\u54c1\u56fe\u7247', blank=True)),
                ('supplier_name', models.CharField(max_length=128, verbose_name='\u4f9b\u5e94\u5546\u540d\u79f0', blank=True)),
                ('pay_num', models.IntegerField(default=0, verbose_name='\u4ed8\u6b3e\u6570\u91cf')),
                ('no_pay_num', models.IntegerField(default=0, verbose_name='\u672a\u4ed8\u6b3e\u6570\u91cf')),
                ('cancel_num', models.IntegerField(default=0, verbose_name='\u53d1\u8d27\u524d\u9000\u6b3e\u6570\u91cf')),
                ('out_stock_num', models.IntegerField(default=0, verbose_name='\u7f3a\u8d27\u9000\u6b3e\u6570\u91cf')),
                ('return_good_num', models.IntegerField(default=0, verbose_name='\u9000\u8d27\u9000\u6b3e\u6570\u91cf')),
                ('payment', models.FloatField(default=0, verbose_name='\u9500\u552e\u989d')),
                ('agent_price', models.FloatField(default=0, verbose_name='\u51fa\u552e\u4ef7(\u4ef6)')),
                ('cost', models.FloatField(default=0, verbose_name='\u6210\u672c\u4ef7')),
            ],
            options={
                'db_table': 'statistics_model_stats',
                'verbose_name': '\u6b3e\u5f0f\u7edf\u8ba1\u8868',
                'verbose_name_plural': '\u6b3e\u5f0f\u7edf\u8ba1\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='modelstats',
            unique_together=set([('sale_product', 'upshelf_time', 'offshelf_time')]),
        ),
    ]
