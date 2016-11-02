# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0008_create_table_weixin_qrcode_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='weixintplmsg',
            name='created',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 24, 19, 33, 28, 838382), auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weixintplmsg',
            name='modified',
            field=models.DateTimeField(default=datetime.datetime(2016, 9, 24, 19, 33, 35, 342185), auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='weixintplmsg',
            name='template_ids',
            field=jsonfield.fields.JSONField(default={}, max_length=512, verbose_name='\u83dc\u5355\u4ee3\u7801', blank=True),
        ),
    ]
