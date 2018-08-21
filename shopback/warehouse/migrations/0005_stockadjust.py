# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0010_stats_add_adjust'),
        ('warehouse', '0004_receiptgoods_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockAdjust',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('ware_by', models.IntegerField(default=0, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3')])),
                ('num', models.IntegerField(default=0, verbose_name='\u8c03\u6574\u6570')),
                ('inferior', models.BooleanField(default=False, verbose_name='\u6b21\u54c1')),
                ('status', models.IntegerField(choices=[(0, '\u521d\u59cb'), (1, '\u5df2\u5904\u7406'), (-1, '\u5df2\u4f5c\u5e9f')])),
                ('sku', models.ForeignKey(verbose_name='SKU', to='items.ProductSku', null=True)),
            ],
            options={
                'db_table': 'shop_ware_stock_adjust',
                'verbose_name': '\u5e93\u5b58\u8c03\u6574',
                'verbose_name_plural': '\u5e93\u5b58\u8c03\u6574\u5217\u8868',
            },
        ),
    ]
