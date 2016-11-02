# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0003_add_sku_num_oid_outer_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageorder',
            name='sku_num',
            field=models.IntegerField(default=0, verbose_name='SKU\u79cd\u7c7b\u6570'),
        ),
    ]
