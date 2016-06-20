# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0017_inbound_forecast_inbound_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='purchase_detail_unikey',
            field=models.CharField(max_length=32, unique=True, null=True, verbose_name=b'PurchaseDetailUniKey'),
        ),
        migrations.AddField(
            model_name='orderdetail',
            name='purchase_order_unikey',
            field=models.CharField(db_index=True, max_length=32, verbose_name=b'PurchaseOrderUnikey', blank=True),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='purchase_order_unikey',
            field=models.CharField(max_length=32, unique=True, null=True, verbose_name='PurchaseOrderUnikey'),
        ),
        migrations.AddField(
            model_name='purchaserecord',
            name='note',
            field=models.CharField(max_length=128, verbose_name='\u5907\u6ce8\u4fe1\u606f', blank=True),
        ),
        migrations.AlterField(
            model_name='orderdetail',
            name='orderlist',
            field=models.ForeignKey(related_name='order_list', verbose_name='\u8ba2\u5355\u7f16\u53f7', to='dinghuo.OrderList', null=True),
        ),
        migrations.AlterField(
            model_name='purchasearrangement',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u9000\u8d27\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='purchaserecord',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u9000\u8d27\u53d6\u6d88')]),
        ),
    ]
