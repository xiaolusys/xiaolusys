# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apprelease', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='apprelease',
            name='hash_value',
            field=models.CharField(max_length=32, unique=True, null=True, verbose_name='md5hash'),
        ),
        migrations.AddField(
            model_name='apprelease',
            name='version_code',
            field=models.IntegerField(default=0, verbose_name='\u5ba2\u6237\u7aef\u7248\u672c\u53f7'),
        ),
        migrations.AlterField(
            model_name='apprelease',
            name='version',
            field=models.CharField(max_length=128, verbose_name='\u5ba2\u6237\u7aef\u7248\u672c', db_index=True),
        ),
    ]
