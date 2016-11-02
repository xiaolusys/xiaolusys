# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0004_packageorder_sku_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='assign_time',
            field=models.DateTimeField(null=True, verbose_name='\u5206\u914dSKU\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='cancel_time',
            field=models.DateTimeField(null=True, verbose_name='\u53d6\u6d88\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='finish_time',
            field=models.DateTimeField(null=True, verbose_name='\u5b8c\u6210\u65f6\u95f4', db_index=True),
        ),
    ]
