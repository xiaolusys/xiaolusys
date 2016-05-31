# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0012_auto_20160530_2224'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='useraddresschange',
            options={'verbose_name': '\u7528\u6237\u4fee\u6539\u5730\u5740', 'verbose_name_plural': '\u7528\u6237\u4fee\u6539\u5730\u5740\u5386\u53f2'},
        ),
        migrations.AlterField(
            model_name='useraddresschange',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u5b8c\u6210'), (2, '\u5931\u8d25')]),
        ),
    ]
