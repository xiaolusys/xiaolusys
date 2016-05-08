# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0007_create_dirty_merge_trade_and_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='package_order_pid',
            field=models.CharField(db_index=True, max_length=100, null=True, verbose_name='\u5305\u88f9ID', blank=True),
        ),
    ]
