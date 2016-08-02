# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorder', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='closed_time',
            field=models.DateTimeField(null=True, verbose_name='\u5173\u95ed\u65e5\u671f', db_index=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='start_time',
            field=models.DateTimeField(null=True, verbose_name='\u5f00\u59cb\u5904\u7406\u65e5\u671f', db_index=True),
        ),
    ]
