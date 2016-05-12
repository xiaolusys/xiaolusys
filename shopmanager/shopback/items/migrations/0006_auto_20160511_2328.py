# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0005_auto_20160429_2052'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productskustats',
            name='product_id',
            field=models.IntegerField(null=True, verbose_name='\u5546\u54c1ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='productskustats',
            name='sku_id',
            field=models.IntegerField(unique=True, null=True, verbose_name='SKUID'),
        ),
    ]
