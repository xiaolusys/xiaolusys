# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0021_auto_20160622_1718'),
    ]

    operations = [
        migrations.AddField(
            model_name='returngoods',
            name='type',
            field=models.IntegerField(default=0, verbose_name='\u9000\u8d27\u7c7b\u578b', choices=[(0, '\u666e\u901a\u9000\u8d27'), (1, '\u672a\u5165\u5e93\u9000\u8d27')]),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='\u8fdb\u5ea6', choices=[(0, '\u4f5c\u5e9f'), (1, '\u5f85\u5206\u914d'), (2, '\u5f85\u8d28\u68c0'), (3, '\u5b8c\u6210')]),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='wrong',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u9519\u8d27'),
        ),
    ]
