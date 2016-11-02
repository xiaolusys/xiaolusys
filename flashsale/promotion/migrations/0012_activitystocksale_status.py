# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0011_auto_20160823_1501'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitystocksale',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u786e\u8ba4\u552e\u54c1'), (2, '\u786e\u8ba4\u5e93\u5b58'), (3, '\u4e0a\u67b6\u552e\u5356'), (4, '\u5df2\u5b8c\u6210'), (5, '\u5df2\u5220\u9664')]),
        ),
    ]
