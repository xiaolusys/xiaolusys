# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0045_orderlist_pdistrict_null'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PurchaseRecord',
        ),
        migrations.AddField(
            model_name='purchasearrangement',
            name='gen_order',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='created_by',
            field=models.SmallIntegerField(default=1, verbose_name='\u521b\u5efa\u65b9\u5f0f', choices=[(1, '\u624b\u5de5\u8ba2\u8d27'), (2, '\u8ba2\u5355\u81ea\u52a8\u8ba2\u8d27'), (3, '\u8865\u8d27')]),
        ),
        migrations.AlterField(
            model_name='supplychainstatsorder',
            name='sale_time',
            field=models.DateField(verbose_name='\u7edf\u8ba1\u65f6\u95f4', db_index=True),
        ),
    ]
