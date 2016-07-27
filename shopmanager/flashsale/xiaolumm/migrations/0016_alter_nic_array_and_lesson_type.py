# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0015_create_mamavebviewconf'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lessontopic',
            name='lesson_type',
            field=models.IntegerField(default=0, verbose_name='\u7c7b\u578b', choices=[(3, '\u57fa\u7840\u8bfe\u7a0b'), (0, '\u8bfe\u7a0b'), (1, '\u5b9e\u6218'), (2, '\u77e5\u8bc6')]),
        ),
        migrations.AlterField(
            model_name='ninepicadver',
            name='pic_arry',
            field=jsonfield.fields.JSONField(default=[], max_length=2048, null=True, verbose_name='\u56fe\u7247\u94fe\u63a5', blank=True),
        ),
    ]
