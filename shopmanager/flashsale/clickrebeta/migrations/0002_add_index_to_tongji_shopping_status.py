# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clickrebeta', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='statisticsshopping',
            name='status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u8ba2\u5355\u72b6\u6001', choices=[(0, '\u5df2\u4ed8\u6b3e'), (1, '\u5df2\u5b8c\u6210'), (2, '\u5df2\u53d6\u6d88')]),
        ),
    ]
