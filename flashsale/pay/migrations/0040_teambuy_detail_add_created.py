# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0039_teambuy_share_xlmm_id_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='teambuydetail',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 1, 16, 3, 4, 329869), auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='teambuydetail',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 1, 16, 3, 13, 841810), auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
            preserve_default=False,
        )
    ]
