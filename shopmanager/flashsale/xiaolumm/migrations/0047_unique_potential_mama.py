# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0046_add_mama_mission_award'),
    ]

    operations = [
        migrations.AlterField(
            model_name='potentialmama',
            name='potential_mama',
            field=models.IntegerField(unique=True, verbose_name='\u6f5c\u5728\u5988\u5988\u4e13\u5c5eid', db_index=True),
        ),
    ]
