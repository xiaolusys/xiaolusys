# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0010_add_together_index_on_shoppingcart'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAddressChange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('new_id', models.IntegerField(verbose_name='\u65b0\u5730\u5740ID', db_index=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u5b8c\u6210')])),
                ('cus_uid', models.BigIntegerField(verbose_name='\u5ba2\u6237ID', db_index=True)),
                ('old_id', models.IntegerField(verbose_name='\u8001\u5730\u5740ID', db_index=True)),
                ('receiver_name', models.CharField(max_length=25, verbose_name='\u6536\u8d27\u4eba\u59d3\u540d', blank=True)),
                ('receiver_state', models.CharField(max_length=16, verbose_name='\u7701', blank=True)),
                ('receiver_city', models.CharField(max_length=16, verbose_name='\u5e02', blank=True)),
                ('receiver_district', models.CharField(max_length=16, verbose_name='\u533a', blank=True)),
                ('receiver_address', models.CharField(max_length=128, verbose_name='\u8be6\u7ec6\u5730\u5740', blank=True)),
                ('receiver_zip', models.CharField(max_length=10, verbose_name='\u90ae\u7f16', blank=True)),
                ('receiver_mobile', models.CharField(db_index=True, max_length=11, verbose_name='\u624b\u673a', blank=True)),
                ('receiver_phone', models.CharField(max_length=20, verbose_name='\u7535\u8bdd', blank=True)),
                ('logistic_company_code', models.CharField(max_length=16, verbose_name='\u4f18\u5148\u5feb\u9012\u7f16\u7801', blank=True)),
                ('package_order_ids', models.CharField(max_length=100, verbose_name='\u539f\u5305\u88f9id', blank=True)),
                ('sale_trade_id', models.ForeignKey(to='pay.SaleTrade')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
