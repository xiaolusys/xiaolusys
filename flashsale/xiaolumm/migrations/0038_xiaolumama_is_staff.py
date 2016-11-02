# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0037_week_carry_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='xiaolumama',
            name='is_staff',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u7279\u6b8a\u8d26\u53f7\uff08\u516c\u53f8\u804c\u5458\uff09'),
        ),
    ]
