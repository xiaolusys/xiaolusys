# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderAmount',
            fields=[
                ('oid', models.BigIntegerField(serialize=False, primary_key=True)),
                ('num_iid', models.BigIntegerField(null=True)),
                ('title', models.CharField(max_length=64, blank=True)),
                ('sku_id', models.BigIntegerField(null=True)),
                ('sku_properties_name', models.CharField(max_length=128, blank=True)),
                ('num', models.IntegerField(null=True)),
                ('price', models.CharField(max_length=10, blank=True)),
                ('payment', models.CharField(max_length=10, blank=True)),
                ('discount_fee', models.CharField(max_length=10, blank=True)),
                ('adjust_fee', models.CharField(max_length=10, blank=True)),
                ('promotion_name', models.CharField(max_length=64, blank=True)),
            ],
            options={
                'db_table': 'shop_amounts_orderamount',
            },
        ),
        migrations.CreateModel(
            name='TradeAmount',
            fields=[
                ('tid', models.BigIntegerField(serialize=False, primary_key=True)),
                ('buyer_cod_fee', models.CharField(max_length=10, blank=True)),
                ('seller_cod_fee', models.CharField(max_length=10, blank=True)),
                ('express_agency_fee', models.CharField(max_length=10, blank=True)),
                ('alipay_no', models.CharField(max_length=64, blank=True)),
                ('total_fee', models.CharField(max_length=10, blank=True)),
                ('post_fee', models.CharField(max_length=10, blank=True)),
                ('cod_fee', models.CharField(max_length=10, blank=True)),
                ('payment', models.CharField(max_length=10, blank=True)),
                ('commission_fee', models.CharField(max_length=10, blank=True)),
                ('buyer_obtain_point_fee', models.CharField(max_length=10, blank=True)),
                ('promotion_details', models.TextField(max_length=500, blank=True)),
                ('created', models.DateTimeField(null=True)),
                ('pay_time', models.DateTimeField(null=True)),
                ('end_time', models.DateTimeField(null=True)),
                ('year', models.IntegerField(null=True, db_index=True)),
                ('month', models.IntegerField(null=True, db_index=True)),
                ('week', models.IntegerField(null=True, db_index=True)),
                ('day', models.IntegerField(null=True, db_index=True)),
                ('hour', models.CharField(db_index=True, max_length=5, blank=True)),
                ('user', models.ForeignKey(related_name='trade_amounts', to='users.User', null=True)),
            ],
            options={
                'db_table': 'shop_amounts_tradeamount',
            },
        ),
        migrations.AddField(
            model_name='orderamount',
            name='trade_amount',
            field=models.ForeignKey(related_name='order_amounts', to='amounts.TradeAmount'),
        ),
    ]
