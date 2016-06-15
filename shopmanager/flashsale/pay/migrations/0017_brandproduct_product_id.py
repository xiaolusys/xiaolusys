# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0016_add_extrapic_and_brand_locationid'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandproduct',
            name='product_id',
            field=models.BigIntegerField(default=0, verbose_name='\u5546\u54c1ID', db_index=True),
        ),
    ]
