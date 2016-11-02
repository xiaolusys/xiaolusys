# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0022_carry_total_add_level'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessontopic',
            name='cover_image',
            field=models.CharField(max_length=256, verbose_name='\u8bfe\u7a0b\u5c01\u9762\u56fe', blank=True),
        ),
    ]
