# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0004_saleproduct_orderlist_show_memo'),
        ('dinghuo', '0008_auto_20160528_1137'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseArrangement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('package_sku_item_id', models.IntegerField(default=0, verbose_name='\u5305\u88f9ID', db_index=True)),
                ('oid', models.CharField(max_length=32, verbose_name='sku\u4ea4\u6613\u5355\u53f7', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00id ')),
                ('purchase_order_unikey', models.CharField(db_index=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u552f\u4e00id', blank=True)),
                ('purchase_record_unikey', models.CharField(db_index=True, max_length=32, verbose_name='PR\u552f\u4e00id', blank=True)),
                ('outer_id', models.CharField(max_length=32, verbose_name='\u4ea7\u54c1\u5916\u90e8\u7f16\u7801', db_index=True)),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name='\u89c4\u683cID', blank=True)),
                ('sku_id', models.CharField(max_length=32, verbose_name='sku\u5546\u54c1id', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u989c\u8272\u7ea7\u4ea7\u54c1\u540d\u79f0')),
                ('sku_properties_name', models.CharField(max_length=16, verbose_name='\u8d2d\u4e70\u89c4\u683c', blank=True)),
                ('num', models.IntegerField(default=0, verbose_name='\u8ba2\u8d2d\u91cf')),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u9000\u8d27\u53d6\u6d88'), (3, '\u5339\u914d\u53d6\u6d88')])),
                ('purchase_order_status', models.IntegerField(default=1, db_index=True, verbose_name='PO\u72b6\u6001', choices=[(1, b'OPEN'), (2, b'BOOKED'), (3, b'FINISHED'), (4, b'CANCELED')])),
                ('initial_book', models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u5df2\u8ba2\u8d27')),
            ],
            options={
                'db_table': 'flashsale_dinghuo_purchase_arrangement',
                'verbose_name': 'v2/\u8ba2\u8d27\u5206\u914d\u8bb0\u5f55',
                'verbose_name_plural': 'v2/\u8ba2\u8d27\u5206\u914d\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00id ')),
                ('purchase_order_unikey', models.CharField(db_index=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u552f\u4e00ID', blank=True)),
                ('outer_id', models.CharField(max_length=20, verbose_name='\u5546\u54c1\u7f16\u7801', blank=True)),
                ('outer_sku_id', models.CharField(max_length=20, verbose_name='\u89c4\u683cID', blank=True)),
                ('sku_id', models.CharField(max_length=32, verbose_name='sku\u5546\u54c1id', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u4ea7\u54c1\u540d\u79f0')),
                ('sku_properties_name', models.CharField(max_length=16, verbose_name='\u8d2d\u4e70\u89c4\u683c', blank=True)),
                ('book_num', models.IntegerField(default=0, verbose_name='Book\u6570\u91cf')),
                ('need_num', models.IntegerField(default=0, verbose_name='Need\u6570\u91cf')),
                ('extra_num', models.IntegerField(default=0, verbose_name='Extra\u6570\u91cf')),
                ('arrival_num', models.IntegerField(default=0, verbose_name='Arrival\u6570\u91cf')),
                ('inferior_num', models.IntegerField(default=0, verbose_name='\u6b21\u54c1\u6570\u91cf')),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, b'OPEN'), (2, b'BOOKED'), (3, b'FINISHED'), (4, b'CANCELED')])),
                ('unit_price', models.IntegerField(default=0, verbose_name='\u4e70\u5165\u4ef7\u683c')),
                ('total_price', models.IntegerField(default=0, verbose_name='\u5355\u9879\u603b\u4ef7')),
            ],
            options={
                'db_table': 'flashsale_dinghuo_purchase_detail',
                'verbose_name': 'v2/\u8ba2\u8d27\u660e\u7ec6',
                'verbose_name_plural': 'v2/\u8ba2\u8d27\u660e\u7ec6\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('uni_key', models.CharField(db_index=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u552f\u4e00ID', blank=True)),
                ('supplier_id', models.IntegerField(default=0, verbose_name='Supplier ID')),
                ('supplier_name', models.CharField(max_length=128, verbose_name='Supplier\u540d\u79f0')),
                ('book_num', models.IntegerField(default=0, verbose_name='Book\u6570\u91cf')),
                ('need_num', models.IntegerField(default=0, verbose_name='Need\u6570\u91cf')),
                ('arrival_num', models.IntegerField(default=0, verbose_name='Arrival\u6570\u91cf')),
                ('inferior_num', models.IntegerField(default=0, verbose_name='\u6b21\u54c1\u6570\u91cf')),
                ('total_price', models.IntegerField(default=0, verbose_name='\u603b\u4ef7')),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, b'OPEN'), (2, b'BOOKED'), (3, b'FINISHED'), (4, b'CANCELED')])),
            ],
            options={
                'db_table': 'flashsale_dinghuo_purchase_order',
                'verbose_name': 'v2/\u8ba2\u8d27',
                'verbose_name_plural': 'v2/\u8ba2\u8d27\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('package_sku_item_id', models.IntegerField(default=0, verbose_name='\u5305\u88f9ID', db_index=True)),
                ('oid', models.CharField(max_length=32, verbose_name='sku\u4ea4\u6613\u5355\u53f7', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00id ')),
                ('outer_id', models.CharField(max_length=32, verbose_name='\u4ea7\u54c1\u5916\u90e8\u7f16\u7801', db_index=True)),
                ('outer_sku_id', models.CharField(max_length=32, verbose_name='\u89c4\u683cID', blank=True)),
                ('sku_id', models.CharField(max_length=32, verbose_name='sku\u5546\u54c1id', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u989c\u8272\u7ea7\u4ea7\u54c1\u540d\u79f0')),
                ('sku_properties_name', models.CharField(max_length=16, verbose_name='\u8d2d\u4e70\u89c4\u683c', blank=True)),
                ('request_num', models.IntegerField(default=0, verbose_name='Request\u91cf')),
                ('book_num', models.IntegerField(default=0, verbose_name='\u8ba2\u8d2d\u91cf')),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u9000\u8d27\u53d6\u6d88'), (3, '\u5339\u914d\u53d6\u6d88')])),
            ],
            options={
                'db_table': 'flashsale_dinghuo_purchase_record',
                'verbose_name': 'v2/\u8ba2\u5355\u8ba2\u8d27\u8bb0\u5f55',
                'verbose_name_plural': 'v2/\u8ba2\u5355\u8ba2\u8d27\u8bb0\u5f55\u8868',
            },
        ),
        migrations.RemoveField(
            model_name='returngoods',
            name='supplier_id',
        ),
        migrations.AddField(
            model_name='returngoods',
            name='supplier',
            field=models.ForeignKey(verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier', null=True),
        ),
    ]
