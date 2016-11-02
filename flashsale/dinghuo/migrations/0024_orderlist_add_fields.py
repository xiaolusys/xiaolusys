# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0023_inbound_change_status_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='inferior',
            field=models.BooleanField(default=False, verbose_name='\u6709\u6b21\u54c1'),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='lack',
            field=models.BooleanField(default=True, verbose_name='\u7f3a\u8d27'),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='stage',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u8fdb\u5ea6', choices=[(0, '\u8349\u7a3f'), (1, '\u5ba1\u6838'), (2, '\u4ed8\u6b3e'), (3, '\u6536\u8d27'), (4, '\u7ed3\u7b97'), (5, '\u5b8c\u6210')]),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='created_by',
            field=models.SmallIntegerField(default=1, verbose_name='\u521b\u5efa\u65b9\u5f0f', choices=[(1, '\u624b\u5de5\u8ba2\u8d27'), (2, '\u8ba2\u5355\u81ea\u52a8\u8ba2\u8d27')]),
        ),
    ]
