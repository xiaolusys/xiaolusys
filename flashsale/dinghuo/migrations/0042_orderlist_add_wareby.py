# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0041_auto_20160926_1515'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='ware_by',
            field=models.IntegerField(default=0, verbose_name='\u6536\u8d27\u4ed3', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        )
    ]
