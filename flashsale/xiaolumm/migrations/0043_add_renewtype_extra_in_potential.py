# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0042_add_referal_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='potentialmama',
            name='extras',
            field=jsonfield.fields.JSONField(default={}, max_length=512, null=True, verbose_name='\u9644\u52a0\u4fe1\u606f', blank=True),
        ),
        migrations.AddField(
            model_name='potentialmama',
            name='last_renew_type',
            field=models.IntegerField(default=15, verbose_name='\u6700\u540e\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
    ]
