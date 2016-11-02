# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0007_auto_20160524_1028'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orderdetail',
            options={'verbose_name': '\u8ba2\u8d27\u660e\u7ec6\u8868', 'verbose_name_plural': '\u8ba2\u8d27\u660e\u7ec6\u8868', 'permissions': [('change_orderdetail_quantity', '\u4fee\u6539\u8ba2\u8d27\u660e\u7ec6\u6570\u91cf')]},
        ),
    ]
