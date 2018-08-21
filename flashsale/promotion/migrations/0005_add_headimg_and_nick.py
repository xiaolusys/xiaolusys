# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0004_auto_20160507_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='appdownloadrecord',
            name='headimgurl',
            field=models.CharField(max_length=256, verbose_name='\u5934\u56fe', blank=True),
        ),
        migrations.AddField(
            model_name='appdownloadrecord',
            name='nick',
            field=models.CharField(max_length=32, verbose_name='\u6635\u79f0', blank=True),
        ),
    ]
