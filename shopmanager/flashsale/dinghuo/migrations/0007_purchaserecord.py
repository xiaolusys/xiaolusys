# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0006_auto_20160517_1845'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('package_sku_item_id', models.IntegerField(default=0, verbose_name='\u5305\u88f9ID', db_index=True)),
                ('oid', models.CharField(max_length=32, verbose_name='sku\u4ea4\u6613\u5355\u53f7', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00id ')),
                ('purchase_order_unikey', models.CharField(db_index=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u552f\u4e00id', blank=True)),
                ('outer_id', models.CharField(max_length=32, verbose_name='\u4ea7\u54c1\u5916\u90e8\u7f16\u7801', db_index=True)),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name='\u89c4\u683cID', blank=True)),
                ('sku_id', models.CharField(max_length=32, verbose_name='sku\u5546\u54c1id', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u989c\u8272\u7ea7\u4ea7\u54c1\u540d\u79f0')),
                ('sku_properties_name', models.CharField(max_length=16, verbose_name='\u8d2d\u4e70\u89c4\u683c', blank=True)),
                ('num', models.IntegerField(default=0, verbose_name='\u8ba2\u8d2d\u91cf')),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u9000\u8d27\u53d6\u6d88'), (3, '\u5339\u914d\u53d6\u6d88')])),
                ('initial_book', models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u5df2\u8ba2\u8d27')),
            ],
            options={
                'db_table': 'flashsale_dinghuo_purchase_record',
                'verbose_name': 'v2/\u8ba2\u5355\u8ba2\u8d27\u8bb0\u5f55',
                'verbose_name_plural': 'v2/\u8ba2\u5355\u8ba2\u8d27\u8bb0\u5f55\u8868',
            },
        ),
    ]
