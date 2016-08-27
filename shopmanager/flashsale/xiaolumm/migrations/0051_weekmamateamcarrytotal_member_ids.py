# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0050_xiaolumm_add_grandma_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='weekmamateamcarrytotal',
            name='member_ids',
            field=jsonfield.fields.JSONField(default=[], max_length=10240, verbose_name='\u6210\u5458\u5217\u8868'),
        ),
    ]
