# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0042_orderlist_add_wareby'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasearrangement',
            name='purchase_record_unikey',
            field=models.CharField(db_index=True, max_length=64, verbose_name='PR\u552f\u4e00id', blank=True),
        )
    ]
