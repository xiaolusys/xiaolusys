# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0035_mamadailyappvisit'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamadailyappvisit',
            name='device_type',
            field=models.IntegerField(default=0, verbose_name='\u8bbe\u5907', choices=[(0, b'Unknown'), (1, b'Android'), (2, b'IOS')]),
        ),
        migrations.AddField(
            model_name='mamadailyappvisit',
            name='user_agent',
            field=models.CharField(max_length=128, verbose_name='UserAgent', blank=True),
        ),
        migrations.AddField(
            model_name='mamadailyappvisit',
            name='version',
            field=models.CharField(max_length=32, verbose_name='\u7248\u672c\u4fe1\u606f', blank=True),
        ),
    ]
