# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0012_add_model_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleorderstatsrecord',
            name='sale_product',
            field=models.BigIntegerField(default=0, verbose_name='\u9009\u54c1id', db_index=True),
        ),
    ]
