# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0002_modify_salestats_uni_key'),
    ]

    operations = [
        migrations.RenameField(
            model_name='saleorderstatsrecord',
            old_name='outer_sku_id',
            new_name='sku_id',
        ),
        migrations.AddField(
            model_name='saleorderstatsrecord',
            name='outer_id',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u5916\u90e8\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='salestats',
            name='record_type',
            field=models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'), (16, '\u603b\u8ba1\u7ea7')]),
        ),
    ]
