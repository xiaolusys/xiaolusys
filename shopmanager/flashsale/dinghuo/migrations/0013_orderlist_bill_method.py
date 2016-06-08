# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0012_auto_20160603_2121'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='bill_method',
            field=models.IntegerField(default=11, verbose_name='\u4ed8\u6b3e\u7c7b\u578b', choices=[(11, '\u8d27\u5230\u4ed8\u6b3e'), (12, '\u9884\u4ed8\u6b3e'), (13, '\u4ed8\u6b3e\u63d0\u8d27'), (14, '\u5176\u5b83')]),
        ),
    ]
