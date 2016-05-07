# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0004_auto_20160504_1527'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u5df2\u5b8c\u6210'), (3, '\u53d6\u6d88')]),
        ),
    ]
