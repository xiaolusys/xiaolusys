# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0015_create_mamavebviewconf'),
    ]

    operations = [
        migrations.AddField(
            model_name='xiaolumama',
            name='head_img_url',
            field=models.CharField(default=None, max_length=100, null=True, verbose_name='\u7528\u6237\u5fae\u4fe1\u5934\u50cf'),
        ),
        migrations.AddField(
            model_name='xiaolumama',
            name='nick',
            field=models.CharField(default=None, max_length=100, null=True, verbose_name='\u7528\u6237\u5fae\u4fe1\u6635\u79f0'),
        ),
        migrations.AddField(
            model_name='xiaolumama',
            name='open_id',
            field=models.CharField(default=None, max_length=100, null=True, verbose_name='\u7528\u6237\u5fae\u4fe1openid'),
        ),
    ]
