# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductSkuSaleStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uni_key', models.CharField(max_length=32, unique=True, null=True, verbose_name=b'UNIQUE ID')),
                ('sku_id', models.IntegerField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81SKU\xe8\xae\xb0\xe5\xbd\x95ID', db_index=True)),
                ('product_id', models.IntegerField(null=True, verbose_name=b'\xe5\x95\x86\xe5\x93\x81\xe8\xae\xb0\xe5\xbd\x95ID', db_index=True)),
                ('init_waitassign_num', models.IntegerField(default=0, verbose_name=b'\xe4\xb8\x8a\xe6\x9e\xb6\xe5\x89\x8d\xe5\xbe\x85\xe5\x88\x86\xe9\x85\x8d\xe6\x95\xb0')),
                ('num', models.IntegerField(default=0, verbose_name=b'\xe4\xb8\x8a\xe6\x9e\xb6\xe6\x9c\x9f\xe9\x97\xb4\xe8\xb4\xad\xe4\xb9\xb0\xe6\x95\xb0')),
                ('sale_start_time', models.DateTimeField(db_index=True, null=True, verbose_name=b'\xe5\xbc\x80\xe5\xa7\x8b\xe6\x97\xb6\xe9\x97\xb4', blank=True)),
                ('sale_end_time', models.DateTimeField(db_index=True, null=True, verbose_name=b'\xe7\xbb\x93\xe6\x9d\x9f\xe6\x97\xb6\xe9\x97\xb4', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xb6\xe9\x97\xb4', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xb6\xe9\x97\xb4', null=True)),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', choices=[(0, b'EFFECT'), (1, b'DISCARD'), (2, b'FINISH')])),
            ],
            options={
                'db_table': 'shop_items_productskusalestats',
                'verbose_name': '\u5e93\u5b58/\u5546\u54c1\u8d2d\u4e70\u7edf\u8ba1\u6570\u636e',
                'verbose_name_plural': '\u5e93\u5b58/\u5546\u54c1\u8d2d\u4e70\u7edf\u8ba1\u6570\u636e\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ProductSkuStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('sku_id', models.IntegerField(unique=True, null=True, verbose_name='\u5546\u54c1SKU\u8bb0\u5f55ID')),
                ('product_id', models.IntegerField(null=True, verbose_name='\u5546\u54c1\u8bb0\u5f55ID', db_index=True)),
                ('assign_num', models.IntegerField(default=0, verbose_name='\u5206\u914d\u6570')),
                ('inferior_num', models.IntegerField(default=0, verbose_name='\u6b21\u54c1\u6570')),
                ('history_quantity', models.IntegerField(default=0, verbose_name='\u5386\u53f2\u5e93\u5b58\u6570')),
                ('inbound_quantity', models.IntegerField(default=0, verbose_name='\u5165\u4ed3\u5e93\u5b58\u6570')),
                ('post_num', models.IntegerField(default=0, verbose_name='\u5df2\u53d1\u8d27\u6570')),
                ('sold_num', models.IntegerField(default=0, verbose_name='\u5df2\u88ab\u8d2d\u4e70\u6570')),
                ('shoppingcart_num', models.IntegerField(default=0, verbose_name='\u52a0\u5165\u8d2d\u7269\u8f66\u6570')),
                ('waitingpay_num', models.IntegerField(default=0, verbose_name='\u7b49\u5f85\u4ed8\u6b3e\u6570')),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='\u521b\u5efa\u65f6\u95f4', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4', null=True)),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, b'EFFECT'), (1, b'DISCARD')])),
            ],
            options={
                'db_table': 'shop_items_productskustats',
                'verbose_name': '\u5e93\u5b58/\u5546\u54c1\u7edf\u8ba1\u6570\u636e',
                'verbose_name_plural': '\u5e93\u5b58/\u5546\u54c1\u7edf\u8ba1\u6570\u636e\u5217\u8868',
            },
        ),
        migrations.RemoveField(
            model_name='productsku',
            name='assign_num',
        ),
    ]
