# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0014_change_package_sku_item_verbose_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='purchase_order_unikey',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u552f\u4e00ID', blank=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='assign_status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u5907\u8d27'), (1, '\u5df2\u5907\u8d27'), (2, '\u5df2\u51fa\u8d27'), (3, '\u5df2\u53d6\u6d88')]),
        ),
    ]
