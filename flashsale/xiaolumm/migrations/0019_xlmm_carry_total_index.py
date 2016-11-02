# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0018_xlmm_carry_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrytotalrecord',
            name='record_time',
            field=models.DateTimeField(null=True, verbose_name='\u8bb0\u5f55\u6279\u6b21\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='carrytotalrecord',
            name='type',
            field=models.IntegerField(default=0, db_index=True, choices=[(0, '\u6bcf\u5468\u7edf\u8ba1'), (1, '\u6d3b\u52a8\u7edf\u8ba1')]),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='record_time',
            field=models.DateTimeField(null=True, verbose_name='\u8bb0\u5f55\u6279\u6b21\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='type',
            field=models.IntegerField(default=0, db_index=True, choices=[(0, '\u6bcf\u5468\u7edf\u8ba1'), (1, '\u6d3b\u52a8\u7edf\u8ba1')]),
        ),
        migrations.AlterField(
            model_name='carrytotalrecord',
            name='stat_time',
            field=models.DateTimeField(verbose_name='\u7edf\u8ba1\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='duration_num',
            field=models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u8ba2\u5355\u6570\u91cf'),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='duration_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='history_num',
            field=models.IntegerField(default=0, verbose_name='\u5386\u53f2\u8ba2\u5355\u6570\u91cf', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 24, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='total_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206,\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u603b\u6392\u540d', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='duration_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 24, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='total_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206,\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u603b\u6392\u540d', db_index=True),
        ),
        migrations.AlterField(
            model_name='teamcarrytotalrecord',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 24, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
    ]
