# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import supplychain.supplier.models.category


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0019_add_field_salecategory_cid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salecategory',
            name='cid',
            field=models.IntegerField(default=supplychain.supplier.models.category.default_salecategory_cid, unique=True, verbose_name='\u7c7b\u76eeID'),
        ),
    ]
