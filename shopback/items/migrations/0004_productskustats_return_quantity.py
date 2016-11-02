# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0003_add_outer_id_and_outer_sku_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='productskustats',
            name='return_quantity',
            field=models.IntegerField(default=0, verbose_name='\u9000\u8d27\u6570'),
        ),
    ]
