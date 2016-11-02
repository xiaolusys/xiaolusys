# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0001_initial2'),
    ]

    operations = [
        migrations.AlterField(
            model_name='salestats',
            name='uni_key',
            field=models.CharField(unique=True, max_length=64, verbose_name='\u552f\u4e00\u6807\u8bc6'),
        ),
    ]
