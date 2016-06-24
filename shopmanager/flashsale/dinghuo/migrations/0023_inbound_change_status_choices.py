# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0022_auto_20160622_1743'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inbound',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='\u8fdb\u5ea6', choices=[(0, '\u4f5c\u5e9f'), (1, '\u5f85\u5206\u914d'), (2, '\u5f85\u8d28\u68c0'), (3, '\u5df2\u5165\u5e93'), (4, '\u5df2\u5b8c\u7ed3')]),
        ),
    ]
