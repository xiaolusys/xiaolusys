# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0013_auto_20161025_2023'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='type',
            field=models.IntegerField(default=0, verbose_name='\u5546\u54c1\u7c7b\u578b', choices=[(0, '\u5546\u54c1'), (1, '\u865a\u62df\u5546\u54c1'), (2, '\u975e\u5356\u54c1')]),
        ),
    ]
