# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0031_rgdetail_add_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbound',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3')]),
        )
    ]
