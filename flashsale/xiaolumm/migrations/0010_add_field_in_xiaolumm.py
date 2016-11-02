# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0009_add_field_ninepicadver_detail_modelids'),
    ]

    operations = [
        migrations.AddField(
            model_name='xiaolumama',
            name='renew_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u4e0b\u6b21\u7eed\u8d39\u65f6\u95f4', blank=True),
        )
    ]
