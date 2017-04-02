# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0030_orderlist_set_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='rgdetail',
            name='src',
            field=models.IntegerField(default=0, help_text='0\u6216\u5165\u5e93\u5355id', verbose_name='\u6765\u6e90'),
        ),
        migrations.AddField(
            model_name='rgdetail',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, '\u9000\u8d27\u6536\u6b3e'), (1, '\u9000\u8d27\u66f4\u6362')]),
        )
    ]
