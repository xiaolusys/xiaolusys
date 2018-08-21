# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0006_add_extras_to_weixinfans'),
    ]

    operations = [
        migrations.AddField(
            model_name='weixinfans',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 19, 14, 57, 8, 454035), auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weixinfans',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 19, 14, 57, 21, 77765), auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='weixinfans',
            name='extras',
            field=jsonfield.fields.JSONField(default={b'qrscene': b'0'}, max_length=512, verbose_name='\u989d\u5916\u53c2\u6570'),
        ),
    ]
