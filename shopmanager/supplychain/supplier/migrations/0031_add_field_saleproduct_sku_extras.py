# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0030_add_field_preferencepool_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproduct',
            name='sku_extras',
            field=jsonfield.fields.JSONField(default=[], max_length=10240, verbose_name='sku\u4fe1\u606f'),
        ),
    ]
