# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0052_rank_activity'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitymamateamcarrytotal',
            name='member_ids',
            field=jsonfield.fields.JSONField(default=[], max_length=10240, verbose_name='\u6210\u5458\u5217\u8868'),
        ),
        migrations.AlterField(
            model_name='rankactivity',
            name='end_time',
            field=models.DateField(help_text='9\u670814\u65e50\u70b9\u7ed3\u675f\u5219\u90099\u670813\u65e5', verbose_name='\u6d3b\u52a8\u7ed3\u675f\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='rankactivity',
            name='start_time',
            field=models.DateField(help_text='9\u670812\u65e50\u70b9\u5f00\u59cb\u5219\u90099\u670812\u65e5', verbose_name='\u6d3b\u52a8\u5f00\u59cb\u65f6\u95f4'),
        ),
    ]
