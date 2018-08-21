# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shopback.refunds.models


class Migration(migrations.Migration):

    dependencies = [
        ('refunds', '0002_auto_20160422_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='refundproduct',
            name='sku_id',
            field=models.IntegerField(null=True, verbose_name=b'SKUID'),
        ),
        migrations.AlterField(
            model_name='refund',
            name='id',
            field=models.BigIntegerField(default=shopback.refunds.models.default_refund_no, serialize=False, verbose_name=b'ID', primary_key=True),
        ),
    ]
