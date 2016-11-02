# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReceiptGoods',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('receipt_type', models.IntegerField(default=2, db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(0, '\u5176\u4ed6'), (1, '\u7528\u6237\u9000\u8d27'), (2, '\u91c7\u8d2d\u8ba2\u8d27')])),
                ('weight', models.FloatField(default=0.0, verbose_name='\u91cd\u91cf')),
                ('weight_time', models.DateTimeField(null=True, verbose_name='\u79f0\u91cd\u65f6\u95f4', blank=True)),
                ('express_no', models.CharField(max_length=64, verbose_name='\u5feb\u9012\u53f7', db_index=True)),
                ('express_company', models.IntegerField(verbose_name='\u5feb\u9012\u516c\u53f8', db_index=True)),
                ('memo', models.TextField(max_length=256, null=True, verbose_name='\u5907\u6ce8', blank=True)),
            ],
            options={
                'db_table': 'shop_ware_house_receipt',
                'verbose_name': '\u4ed3\u5e93\u6536\u8d27',
                'verbose_name_plural': '\u4ed3\u5e93\u6536\u8d27\u5217\u8868',
            },
        ),
    ]
