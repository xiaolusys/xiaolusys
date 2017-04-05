# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0033_add_unique_to_purchaseorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbound',
            name='inferior',
            field=models.BooleanField(default=False, verbose_name='\u6709\u6b21\u54c1'),
        )
    ]
