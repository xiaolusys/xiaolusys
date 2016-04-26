# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logistics',
            name='tid',
            field=models.BigIntegerField(serialize=False, primary_key=True),
        ),
    ]
