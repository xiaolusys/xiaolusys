# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='StatisticSaleNum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('upper_grade', models.BigIntegerField(db_index=True, null=True, verbose_name='\u4e0a\u4e00\u7ea7id', blank=True)),
                ('target_id', models.BigIntegerField(verbose_name='\u7ea7\u522b\u5bf9\u5e94instance_id', db_index=True)),
                ('pay_date', models.DateField(verbose_name='\u4ed8\u6b3e\u65e5\u671f', db_index=True)),
                ('uniq_id', models.CharField(max_length=32, verbose_name='\u552f\u4e00\u6807\u8bc6', db_index=True)),
                ('record_type', models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (10, '\u7c7b\u522b\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (16, '\u603b\u8ba1\u7ea7')])),
                ('sale_num', models.IntegerField(default=0, verbose_name='\u9500\u552e\u6570\u91cf')),
                ('sale_value', models.FloatField(default=0, verbose_name='\u9500\u552e\u91d1\u989d')),
                ('stock_out_num', models.IntegerField(default=0, verbose_name='\u7f3a\u8d27\u6570\u91cf')),
                ('before_post_ref_num', models.IntegerField(default=0, verbose_name='\u53d1\u8d27\u524d\u9000\u8d27\u6570\u91cf')),
                ('after_post_ref_num', models.IntegerField(default=0, verbose_name='\u53d1\u8d27\u540e\u9000\u8d27\u6570\u91cf')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
