# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0031_add_field_saleproduct_sku_extras'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferencepool',
            name='is_sku',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u662fsku\u5c5e\u6027'),
        ),
    ]
