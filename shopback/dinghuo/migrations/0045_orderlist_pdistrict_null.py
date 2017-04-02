# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0044_auto_20161012_1136'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inbound',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='p_district',
            field=models.CharField(default='1', max_length=32, null=True, verbose_name='\u5730\u533a', choices=[('1', '\u6c5f\u6d59\u6caa\u7696'), ('2', '\u5c71\u4e1c'), ('3', '\u5e7f\u4e1c\u798f\u5efa')]),
        )
    ]
