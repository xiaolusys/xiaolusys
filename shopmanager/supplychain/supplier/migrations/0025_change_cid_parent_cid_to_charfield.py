# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import supplychain.supplier.models.category


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0024_auto_20160805_2100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salecategory',
            name='cid',
            field=models.CharField(default=supplychain.supplier.models.category.default_salecategory_cid, unique=True, max_length=32, verbose_name='\u7c7b\u76eeID'),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='parent_cid',
            field=models.CharField(default=b'0', max_length=32, verbose_name='\u7236\u7c7b\u76eeID', db_index=True),
        ),
    ]
