# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0026_orderlist_add_press'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='purchase_total_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u4ef6\u6570'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='inferior',
            field=models.BooleanField(default=False, verbose_name='\u6b21\u54c1'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='is_postpay',
            field=models.BooleanField(default=False, verbose_name='\u540e\u4ed8'),
        ),
    ]
