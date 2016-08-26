# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0027_add_qqweixin_suppliername_index'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesupplier',
            name='return_ware_by',
            field=models.SmallIntegerField(default=0, verbose_name='\u9000\u8d27\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='salesupplier',
            name='ware_by',
            field=models.SmallIntegerField(default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
    ]
