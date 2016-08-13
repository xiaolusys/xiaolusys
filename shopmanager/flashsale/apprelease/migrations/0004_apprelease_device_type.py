# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apprelease', '0003_add_update_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='apprelease',
            name='device_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u8bbe\u5907', choices=[(0, b'Unknown'), (1, b'Android'), (2, b'IOS')]),
        ),
    ]
