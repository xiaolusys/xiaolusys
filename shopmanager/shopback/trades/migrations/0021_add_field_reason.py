# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0020_add_failed_retrieve_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='tradewuliu',
            name='reason',
            field=models.CharField(max_length=128, verbose_name='\u539f\u56e0', blank=True),
        ),
    ]
