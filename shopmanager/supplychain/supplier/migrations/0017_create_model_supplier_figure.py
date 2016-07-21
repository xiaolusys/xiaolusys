# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0016_unique_manager_detail'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplierFigure',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('schedule_num', models.IntegerField(default=0, verbose_name='\u9009\u6b3e\u6570\u91cf')),
                ('no_pay_num', models.IntegerField(default=0, verbose_name='\u672a\u4ed8\u6b3e\u6570\u91cf')),
                ('pay_num', models.IntegerField(default=0, verbose_name='\u4ed8\u6b3e\u6570\u91cf')),
                ('cancel_num', models.IntegerField(default=0, verbose_name='\u53d1\u8d27\u524d\u9000\u6b3e\u6570\u91cf')),
                ('out_stock_num', models.IntegerField(default=0, verbose_name='\u7f3a\u8d27\u9000\u6b3e\u6570\u91cf')),
                ('return_good_num', models.IntegerField(default=0, verbose_name='\u9000\u8d27\u9000\u6b3e\u6570\u91cf')),
                ('return_good_rate', models.FloatField(default=0.0, verbose_name='\u9000\u8d27\u7387', db_index=True)),
                ('payment', models.FloatField(default=0.0, verbose_name='\u9500\u552e\u91d1\u989d')),
                ('cancel_amount', models.FloatField(default=0.0, verbose_name='\u53d1\u8d27\u524d\u9000\u6b3e\u91d1\u989d')),
                ('out_stock_amount', models.FloatField(default=0.0, verbose_name='\u7f3a\u8d27\u9000\u6b3e\u91d1\u989d')),
                ('return_good_amount', models.FloatField(default=0.0, verbose_name='\u9000\u8d27\u9000\u6b3e\u91d1\u989d')),
                ('avg_post_days', models.FloatField(default=0.0, verbose_name='\u5e73\u5747\u53d1\u8d27\u5929\u6570')),
                ('supplier', models.OneToOneField(related_name='figures', verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier')),
            ],
            options={
                'db_table': 'supplychain_supply_supplier_figure',
                'verbose_name': '\u4f9b\u5e94\u5546/\u6570\u636e\u8868',
                'verbose_name_plural': '\u4f9b\u5e94\u5546/\u6570\u636e\u5217\u8868',
            },
        )
    ]
