# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0008_appdownloadrecord_uni_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityStockSale',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('day_batch_num', models.IntegerField(default=0, verbose_name='\u4e13\u9898\u5e8f\u53f7')),
                ('onshelf_time', models.DateField(verbose_name='\u4e0a\u67b6\u65e5\u671f')),
                ('offshelf_time', models.DateField(verbose_name='\u4e0b\u67b6\u65e5\u671f')),
                ('total', models.IntegerField(default=0, verbose_name='\u9009\u54c1\u603b\u6570')),
                ('product_total', models.IntegerField(default=0, verbose_name='\u5546\u54c1\u603b\u6570')),
                ('sku_total', models.IntegerField(default=0, verbose_name='SKU\u603b\u6570')),
                ('stock_total', models.IntegerField(default=0, verbose_name='\u53ef\u552e\u5e93\u5b58\u603b\u6570')),
                ('activity', models.ForeignKey(verbose_name='\u4e13\u9898\u6d3b\u52a8', to='pay.ActivityEntry', null=True)),
            ],
            options={
                'db_table': 'flashsale_stocksale_activity',
                'verbose_name': '\u6700\u540e\u75af\u62a2\u6d3b\u52a8\u4e13\u9898',
                'verbose_name_plural': '\u6700\u540e\u75af\u62a2\u6d3b\u52a8\u4e13\u9898\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='BatchStockSale',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u6570\u636e\u5b8c\u6210'), (2, '\u5173\u95ed')])),
                ('total', models.IntegerField(default=0, verbose_name='\u9009\u54c1\u603b\u6570')),
                ('product_total', models.IntegerField(default=0, verbose_name='\u5546\u54c1\u603b\u6570')),
                ('sku_total', models.IntegerField(default=0, verbose_name='SKU\u603b\u6570')),
                ('stock_total', models.IntegerField(default=0, verbose_name='\u53ef\u552e\u5e93\u5b58\u603b\u6570')),
                ('expected_time', models.DateField(null=True, verbose_name='\u671f\u671b\u65e5\u671f', blank=True)),
            ],
            options={
                'db_table': 'flashsale_stocksale_batch',
                'verbose_name': '\u6700\u540e\u75af\u62a2\u6d3b\u52a8\u6279\u6b21',
                'verbose_name_plural': '\u6700\u540e\u75af\u62a2\u6d3b\u52a8\u6279\u6b21\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='StockSale',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('quantity', models.IntegerField(verbose_name='\u5f53\u524d\u5e93\u5b58\u6570')),
                ('sku_num', models.IntegerField(default=0, verbose_name='\u5305\u542bsku\u79cd\u6570')),
                ('day_batch_num', models.IntegerField(default=0, verbose_name='\u4e13\u9898\u5e8f\u53f7')),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u5728\u7ebf'), (2, '\u5173\u95ed')])),
                ('stock_safe', models.IntegerField(default=0, verbose_name='\u5e93\u5b58\u72b6\u6001', choices=[(0, '\u672a\u786e\u8ba4'), (1, '\u5df2\u786e\u8ba4'), (2, '\u65e0\u987b\u786e\u8ba4')])),
                ('activity', models.ForeignKey(to='promotion.ActivityStockSale', null=True)),
                ('batch', models.ForeignKey(verbose_name='\u6279\u6b21\u53f7', to='promotion.BatchStockSale')),
                ('product', models.ForeignKey(to='items.Product')),
                ('sale_product', models.ForeignKey(to='supplier.SaleProduct', null=True)),
            ],
            options={
                'db_table': 'flashsale_stocksale',
                'verbose_name': '\u5e93\u5b58\u503e\u9500\u5546\u54c1',
                'verbose_name_plural': '\u5e93\u5b58\u503e\u9500\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='activitystocksale',
            name='batch',
            field=models.ForeignKey(verbose_name='\u6279\u6b21\u53f7', to='promotion.BatchStockSale'),
        ),
    ]
