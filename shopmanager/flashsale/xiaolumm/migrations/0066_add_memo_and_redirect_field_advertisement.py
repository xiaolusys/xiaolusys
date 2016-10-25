# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0065_add_save_times_and share_times'),
    ]

    operations = [
        migrations.AddField(
            model_name='ninepicadver',
            name='memo',
            field=models.CharField(max_length=512, verbose_name='\u5907\u6ce8', blank=True),
        ),
        migrations.AddField(
            model_name='ninepicadver',
            name='redirect_url',
            field=models.CharField(max_length=512, null=True, verbose_name='\u8df3\u8f6c\u5730\u5740', blank=True),
        )
    ]
