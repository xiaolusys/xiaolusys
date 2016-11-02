# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0011_create_model_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelstats',
            name='model_name',
            field=models.CharField(db_index=True, max_length=64, verbose_name='\u6807\u9898', blank=True),
        ),
        migrations.AlterField(
            model_name='modelstats',
            name='category_name',
            field=models.CharField(max_length=64, verbose_name='\u4ea7\u54c1\u7c7b\u522b\u540d\u79f0', db_index=True),
        ),
        migrations.AlterField(
            model_name='modelstats',
            name='supplier_name',
            field=models.CharField(db_index=True, max_length=128, verbose_name='\u4f9b\u5e94\u5546\u540d\u79f0', blank=True),
        ),
    ]
