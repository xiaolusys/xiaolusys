# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0039_create_packagebackorderstats'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='third_package',
            field=models.BooleanField(default=False, verbose_name='\u7b2c\u4e09\u65b9\u53d1\u8d27'),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (4, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='purchase_order_unikey',
            field=models.CharField(max_length=32, unique=True, null=True, verbose_name='\u8ba2\u8d27\u5355\u751f\u6210\u6807\u8bc6'),
        ),
        migrations.AlterField(
            model_name='packagebackorderstats',
            name='backorder_ids',
            field=models.TextField(default=b'', verbose_name='3\u5929\u672a\u53d1\u8d27\u8ba2\u5355ID', blank=True),
        ),
    ]
