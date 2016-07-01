# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0028_orderlist_add_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='arrival_process',
            field=models.IntegerField(default=0, verbose_name='\u5230\u8d27\u5904\u7406', choices=[(0, '\u672a\u5230'), (1, '\u9700\u5904\u7406'), (2, '\u5df2\u50ac\u8d27'), (3, '\u5df2\u5b8c\u6210')]),
        ),
    ]
