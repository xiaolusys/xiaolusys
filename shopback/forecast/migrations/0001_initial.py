# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0007_auto_20160524_1028'),
        ('supplier', '0005_salesupplier_delta_arrive_days'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForecastInbound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('ware_hourse', models.IntegerField(verbose_name='\u6240\u5c5e\u4ed3\u5e93')),
                ('express_code', models.CharField(max_length=32, verbose_name='\u9884\u586b\u5feb\u9012\u516c\u53f8')),
                ('express_no', models.CharField(max_length=32, verbose_name='\u9884\u586b\u8fd0\u5355\u53f7', db_index=True)),
                ('forecast_arrive_time', models.DateTimeField(null=True, verbose_name='\u9884\u6d4b\u5230\u8d27\u65f6\u95f4', blank=True)),
                ('purchaser', models.CharField(max_length=30, verbose_name='\u91c7\u8d2d\u5458', db_index=True)),
                ('status', models.CharField(default=b'draft', max_length=8, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'draft', '\u8349\u7a3f'), (b'approved', '\u5ba1\u6838'), (b'arrived', '\u5230\u8d27'), (b'canceled', '\u53d6\u6d88')])),
                ('relate_order_set', models.ManyToManyField(to='dinghuo.OrderList', verbose_name='\u5173\u8054\u8ba2\u8d27\u5355')),
                ('supplier', models.ForeignKey(related_name='forecast_inbounds', verbose_name='\u4f9b\u5e94\u5546', blank=True, to='supplier.SaleSupplier', null=True)),
            ],
            options={
                'db_table': 'forecast_inbound',
                'verbose_name': '\u9884\u6d4b\u5230\u8d27\u5355',
                'verbose_name_plural': '\u9884\u6d4b\u5230\u8d27\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ForecastInboundDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('product_id', models.IntegerField(verbose_name='\u5546\u54c1ID')),
                ('sku_id', models.IntegerField(verbose_name='\u89c4\u683cID')),
                ('forecast_arrive_num', models.IntegerField(verbose_name=b'\xe9\xa2\x84\xe6\xb5\x8b\xe5\x88\xb0\xe8\xb4\xa7\xe6\x95\xb0\xe9\x87\x8f')),
                ('product_name', models.CharField(max_length=128, verbose_name='\u5546\u54c1\u5168\u79f0')),
                ('product_img', models.CharField(max_length=256, verbose_name='\u5546\u54c1\u56fe\u7247')),
                ('forecast_inbound', models.ForeignKey(verbose_name='\u5173\u8054\u9884\u6d4b\u5355', to='forecast.ForecastInbound')),
            ],
            options={
                'db_table': 'forecast_inbound_detail',
                'verbose_name': '\u9884\u6d4b\u5230\u8d27\u660e\u7ec6',
                'verbose_name_plural': '\u9884\u6d4b\u5230\u8d27\u660e\u7ec6\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='RealInBound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('wave_no', models.CharField(db_index=True, max_length=32, verbose_name='\u5165\u5e93\u6279\u6b21', blank=True)),
                ('ware_hourse', models.IntegerField(default=0, verbose_name='\u6240\u5c5e\u4ed3\u5e93', db_index=True)),
                ('express_code', models.CharField(max_length=32, verbose_name='\u9884\u586b\u5feb\u9012\u516c\u53f8')),
                ('express_no', models.CharField(max_length=32, verbose_name='\u9884\u586b\u8fd0\u5355\u53f7', db_index=True)),
                ('creator', models.CharField(max_length=30, verbose_name='\u5165\u4ed3\u5458', db_index=True)),
                ('inspector', models.CharField(max_length=30, verbose_name='\u68c0\u8d27\u5458', db_index=True)),
                ('memo', models.TextField(max_length=1024, verbose_name='\u5907\u6ce8', blank=True)),
                ('status', models.CharField(default=b'pengding', max_length=30, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'pengding', '\u5f85\u5904\u7406'), (b'completed', '\u5df2\u5165\u5e93'), (b'canceled', '\u5df2\u53d6\u6d88')])),
                ('forecast_inbound', models.ForeignKey(verbose_name='\u5173\u8054\u9884\u6d4b\u5230\u8d27\u5355', to='forecast.ForecastInbound')),
                ('supplier', models.ForeignKey(verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier')),
            ],
            options={
                'db_table': 'forecast_real_inbound',
                'verbose_name': '\u5230\u8d27\u5355',
                'verbose_name_plural': '\u5230\u8d27\u5355\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='RealInBoundDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('product_id', models.IntegerField(verbose_name='\u5546\u54c1ID')),
                ('sku_id', models.IntegerField(verbose_name='\u89c4\u683cID')),
                ('barcode', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u6761\u7801', blank=True)),
                ('product_name', models.CharField(max_length=128, verbose_name='\u5546\u54c1\u5168\u79f0', blank=True)),
                ('product_img', models.CharField(max_length=256, verbose_name='\u5546\u54c1\u56fe\u7247', blank=True)),
                ('arrival_quantity', models.IntegerField(default=0, verbose_name='\u5df2\u5230\u6570\u91cf')),
                ('inferior_quantity', models.IntegerField(default=0, verbose_name='\u6b21\u54c1\u6570\u91cf')),
                ('district', models.CharField(max_length=64, verbose_name='\u5e93\u4f4d', blank=True)),
                ('status', models.CharField(default=b'normal', max_length=8, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'invalid', '\u4f5c\u5e9f')])),
                ('forecast_inbound_detail', models.OneToOneField(related_name='inbound_detail', verbose_name='\u5173\u8054\u9884\u6d4b\u5230\u8d27\u5355\u660e\u7ec6', to='forecast.ForecastInbound')),
                ('inbound', models.ForeignKey(related_name='inbound_details', verbose_name='\u5165\u5e93\u5355', to='forecast.RealInBound')),
            ],
            options={
                'db_table': 'forecast_real_inbounddetail',
                'verbose_name': '\u5230\u8d27\u5355\u660e\u7ec6',
                'verbose_name_plural': '\u5230\u8d27\u5355\u660e\u7ec6\u5217\u8868',
            },
        ),
    ]
