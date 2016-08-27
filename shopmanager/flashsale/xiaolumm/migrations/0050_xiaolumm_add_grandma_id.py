# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0049_create_table_mama_administrator'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mamamission',
            options={'verbose_name': 'V2/\u5988\u5988\u5468\u6fc0\u52b1\u4efb\u52a1', 'verbose_name_plural': 'V2/\u5988\u5988\u5468\u6fc0\u52b1\u4efb\u52a1\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='mamamissionrecord',
            options={'verbose_name': 'V2/\u5988\u5988\u5468\u6fc0\u52b1\u4efb\u52a1\u8bb0\u5f55', 'verbose_name_plural': 'V2/\u5988\u5988\u5468\u6fc0\u52b1\u4efb\u52a1\u8bb0\u5f55\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='referalrelationship',
            name='referal_from_grandma_id',
            field=models.BigIntegerField(default=0, verbose_name='\u5988\u5988\u7684\u5988\u5988id', db_index=True),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u65b0\u624b\u4efb\u52a1'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u63a8\u8350\u65b0\u624b\u4efb\u52a1'), (7, '\u4e00\u5143\u9080\u8bf7'), (8, '\u5173\u6ce8\u516c\u4f17\u53f7')]),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 26, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 26, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='teamcarrytotalrecord',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 8, 26, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
    ]
