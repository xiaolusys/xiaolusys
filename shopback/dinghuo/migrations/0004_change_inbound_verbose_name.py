# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0003_add_index_statsorder_created_update'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inbound',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u4f5c\u5e9f'), (1, '\u5f85\u5904\u7406'), (2, '\u5b8c\u6210')]),
        ),
    ]
