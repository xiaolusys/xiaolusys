# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0063_add_category_ninepic_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='ninepicadver',
            name='save_times',
            field=models.IntegerField(default=0, verbose_name='\u4fdd\u5b58\u6b21\u6570'),
        ),
        migrations.AddField(
            model_name='ninepicadver',
            name='share_times',
            field=models.IntegerField(default=0, verbose_name='\u5206\u6790\u6b21\u6570'),
        )
]
