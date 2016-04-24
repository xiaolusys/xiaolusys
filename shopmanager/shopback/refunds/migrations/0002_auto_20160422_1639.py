# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('refunds', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refund',
            name='id',
            field=models.BigIntegerField(serialize=False, verbose_name=b'ID', primary_key=True),
        ),
    ]
