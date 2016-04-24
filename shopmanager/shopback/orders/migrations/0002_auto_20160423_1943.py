# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='oid',
            field=models.BigIntegerField(serialize=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='trade',
            name='id',
            field=models.BigIntegerField(serialize=False, primary_key=True),
        ),
    ]
