# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0004_saleproduct_orderlist_show_memo'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesupplier',
            name='delta_arrive_days',
            field=models.IntegerField(default=3, verbose_name='\u9884\u8ba1\u5230\u8d27\u5929\u6570'),
        ),
    ]
