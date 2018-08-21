# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0011_20160517_add_logistics_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='pic_path',
            field=models.CharField(max_length=512, verbose_name='\u5546\u54c1\u56fe\u7247', blank=True),
        ),
    ]
