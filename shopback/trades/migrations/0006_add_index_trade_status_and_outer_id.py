# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0005_auto_20160429_1044'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mergetrade',
            name='status',
            field=models.CharField(blank=True, max_length=32, verbose_name='\u8ba2\u5355\u72b6\u6001', db_index=True, choices=[(b'TRADE_NO_CREATE_PAY', '\u8ba2\u5355\u521b\u5efa'), (b'WAIT_BUYER_PAY', '\u5f85\u4ed8\u6b3e'), (b'WAIT_SELLER_SEND_GOODS', '\u5f85\u53d1\u8d27'), (b'WAIT_BUYER_CONFIRM_GOODS', '\u5f85\u786e\u8ba4\u6536\u8d27'), (b'TRADE_BUYER_SIGNED', '\u8d27\u5230\u4ed8\u6b3e\u7b7e\u6536'), (b'TRADE_FINISHED', '\u4ea4\u6613\u6210\u529f'), (b'TRADE_CLOSED', '\u9000\u6b3e\u4ea4\u6613\u5173\u95ed'), (b'TRADE_CLOSED_BY_TAOBAO', '\u672a\u4ed8\u6b3e\u5173\u95ed')]),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='package_order_id',
            field=models.CharField(db_index=True, max_length=100, null=True, verbose_name='\u5305\u88f9\u7801', blank=True),
        ),
        migrations.AlterIndexTogether(
            name='mergeorder',
            index_together=set([('outer_id', 'outer_sku_id', 'merge_trade')]),
        ),
    ]
