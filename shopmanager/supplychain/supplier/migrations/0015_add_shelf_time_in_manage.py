# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('supplier', '0014_saleproductmanagedetail_order_weight'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproductmanage',
            name='offshelf_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u4e0b\u67b6\u65f6\u95f4', blank=True),
        ),
        migrations.AddField(
            model_name='saleproductmanage',
            name='upshelf_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u4e0a\u67b6\u65f6\u95f4', blank=True),
        ),
    ]
