# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statisticsalenum',
            name='target_id',
            field=models.BigIntegerField(db_index=True, null=True, verbose_name='\u7ea7\u522b\u5bf9\u5e94instance_id', blank=True),
        ),
    ]
