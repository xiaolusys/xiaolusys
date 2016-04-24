# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplier',
            name='supplier_name',
            field=models.CharField(max_length=32, verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86\xe5\x90\x8d\xe7\xa7\xb0', blank=True),
        ),
    ]
