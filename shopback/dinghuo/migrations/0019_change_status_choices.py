# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0018_add_purchase_order_unikey'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasearrangement',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='purchaserecord',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u53d6\u6d88')]),
        ),
    ]
