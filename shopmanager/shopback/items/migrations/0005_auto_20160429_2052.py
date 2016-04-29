# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0004_productskustats_return_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='productskustats',
            name='rg_quantity',
            field=models.IntegerField(default=0, verbose_name='\u9000\u8fd8\u4f9b\u5e94\u5546\u8d27\u6570'),
        ),
        migrations.AlterField(
            model_name='productsku',
            name='outer_id',
            field=models.CharField(max_length=32, verbose_name='\u7f16\u7801'),
        ),
        migrations.AlterField(
            model_name='productskustats',
            name='return_quantity',
            field=models.IntegerField(default=0, verbose_name='\u5ba2\u6237\u9000\u8d27\u6570'),
        ),
    ]
