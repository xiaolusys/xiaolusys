# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0020_hy_inbound'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbound',
            name='check_time',
            field=models.DateTimeField(null=True, verbose_name='\u68c0\u67e5\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='inbounddetail',
            name='check_time',
            field=models.DateTimeField(null=True, verbose_name='\u68c0\u67e5\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='\u8fdb\u5ea6', choices=[(0, '\u4f5c\u5e9f'), (1, '\u5f85\u5206\u914d'), (2, '\u7b49\u5f85\u8d28\u68c0'), (3, '\u5b8c\u6210')]),
        ),
    ]
