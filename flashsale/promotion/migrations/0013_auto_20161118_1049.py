# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0012_activitystocksale_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activitystocksale',
            name='status',
            field=models.IntegerField(choices=[(0, '\u521d\u59cb'), (1, '\u5df2\u786e\u8ba4\u552e\u54c1'), (2, '\u5df2\u786e\u8ba4\u5e93\u5b58'), (3, '\u5df2\u4e0a\u67b6\u552e\u5356'), (4, '\u5df2\u5b8c\u6210'), (5, '\u5df2\u5220\u9664')], default=0, verbose_name='\u72b6\u6001'),
        ),
    ]
