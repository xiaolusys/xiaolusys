# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0032_add_field_preferencepool_is_sku'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saleproduct',
            name='buyer',
            field=models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u91c7\u8d2d\u5458', blank=True),
        ),
        migrations.AlterField(
            model_name='saleproduct',
            name='librarian',
            field=models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u8d44\u6599\u5458', blank=True),
        ),
    ]
