# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0023_skustock_delete_repair'),
    ]

    operations = [
        migrations.CreateModel(
            name='ErpOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('sale_order_oid', models.CharField(unique=True, max_length=32, verbose_name='\u8ba2\u5355oid')),
                ('erp_order_id', models.CharField(max_length=32, verbose_name='ERP\u7cfb\u7edf\u8ba2\u5355ID')),
                ('package_sku_item_id', models.CharField(max_length=32, verbose_name='\u5305\u88f9sku_item_id')),
                ('supplier_id', models.CharField(max_length=32, verbose_name='\u4f9b\u5e94\u5546ID')),
                ('supplier_name', models.CharField(max_length=32, verbose_name='\u4f9b\u5e94\u5546\u540d\u79f0')),
                ('erp_type', models.CharField(default=b'wdt', max_length=16, verbose_name='ERP\u7cfb\u7edf\u7c7b\u578b')),
                ('sync_status', models.CharField(max_length=16, verbose_name='\u540c\u6b65\u72b6\u6001', choices=[(b'success', '\u6210\u529f'), (b'fail', '\u5931\u8d25')])),
                ('sync_result', models.TextField(default=b'', max_length=2048, verbose_name='\u540c\u6b65\u7ed3\u679c', blank=True)),
                ('order_status', models.CharField(default=b'check_trade', max_length=16, verbose_name='\u8ba2\u5355\u72b6\u6001', choices=[(b'cancel_trade', '\u5df2\u53d6\u6d88'), (b'pre_trade', '\u9884\u8ba2\u5355'), (b'check_trade', '\u5f85\u5ba1\u6838'), (b'finance_trade', '\u5f85\u8d22\u5ba1'), (b'wait_send_trade', '\u5f85\u53d1\u8d27'), (b'over_trade', '\u5df2\u5b8c\u6210')])),
                ('logistics_code', models.CharField(max_length=16, verbose_name='\u7269\u6d41\u516c\u53f8\u7f16\u53f7')),
                ('logistics_name', models.CharField(max_length=16, verbose_name='\u7269\u6d41\u516c\u53f8\u540d\u79f0')),
                ('post_id', models.CharField(max_length=16, verbose_name='\u7269\u6d41\u7f16\u53f7')),
                ('delivery_time', models.DateTimeField(verbose_name='\u53d1\u8d27\u65f6\u95f4')),
            ],
            options={
                'db_table': 'shop_trades_erp_orders',
            },
        ),
    ]
