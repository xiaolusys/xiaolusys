# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0043_auto_20161012_1116'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchasearrangement',
            name='uni_key',
            field=models.CharField(unique=True, max_length=64, verbose_name='\u552f\u4e00id '),
        )
    ]
