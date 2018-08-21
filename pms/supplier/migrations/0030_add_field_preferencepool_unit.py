# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0029_create_categorypreference_preferencepool'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferencepool',
            name='unit',
            field=models.CharField(max_length=32, verbose_name='\u5355\u4f4d', blank=True),
        ),
    ]
