# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0016_packageskuitem_book_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageorder',
            name='order_sku_num',
            field=models.IntegerField(default=0, verbose_name='\u7528\u6237\u8ba2\u8d27SKU\u79cd\u7c7b\u603b\u6570'),
        ),
        migrations.AddField(
            model_name='packageorder',
            name='ready_completion',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u5907\u8d27\u5b8c\u6bd5'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='sku_num',
            field=models.IntegerField(default=0, verbose_name='\u5f53\u524dSKU\u79cd\u7c7b\u6570'),
        ),
    ]
