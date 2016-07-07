# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0005_stockadjust'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockadjust',
            name='note',
            field=models.CharField(default=b'', max_length=1000, verbose_name='\u5907\u6ce8', blank=True),
        )
    ]
