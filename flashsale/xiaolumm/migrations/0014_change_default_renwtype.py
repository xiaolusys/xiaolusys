# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0013_rename_mm_field_renewtype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xiaolumama',
            name='last_renew_type',
            field=models.IntegerField(default=365, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
    ]
