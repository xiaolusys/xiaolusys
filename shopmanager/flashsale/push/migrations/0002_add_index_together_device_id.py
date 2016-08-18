# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('push', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pushtopic',
            name='device_id',
            field=models.CharField(max_length=48, verbose_name='\u8bbe\u5907ID', blank=True),
        ),
        migrations.AlterIndexTogether(
            name='pushtopic',
            index_together=set([('device_id', 'platform', 'cat')]),
        ),
    ]
