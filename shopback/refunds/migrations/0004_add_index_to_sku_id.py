# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('refunds', '0003_auto_20160428_1600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refundproduct',
            name='sku_id',
            field=models.IntegerField(null=True, verbose_name=b'SKUID', db_index=True),
        ),
    ]
