# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0028_xiaolufans_change_mama'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamafortune',
            name='invite_all_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u9080\u8bf7\u6570'),
        ),
        migrations.AddField(
            model_name='mamafortune',
            name='invite_trial_num',
            field=models.IntegerField(default=0, verbose_name='\u8bd5\u7528\u5988\u5988\u9080\u8bf7\u6570'),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 29, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 29, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='teamcarrytotalrecord',
            name='stat_time',
            field=models.DateTimeField(default=datetime.datetime(2016, 7, 29, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='xlmmmessage',
            name='dest',
            field=models.CharField(help_text='null\u8868\u793a\u53d1\u7ed9\u4e86\u6240\u6709\u5c0f\u9e7f\u5988\u5988;\u5426\u5219\u586b\u5199django orm\u67e5\u8be2\u6761\u4ef6\u5b57\u5178json', max_length=10000, null=True, verbose_name='\u63a5\u6536\u4eba', blank=True),
        ),
        migrations.AlterField(
            model_name='xlmmmessagerel',
            name='mama',
            field=models.ForeignKey(related_name='rel_messages', verbose_name='\u63a5\u53d7\u8005', to='xiaolumm.XiaoluMama'),
        ),
        migrations.AlterField(
            model_name='xlmmmessagerel',
            name='message',
            field=models.ForeignKey(related_name='rel_messages', to='xiaolumm.XlmmMessage'),
        ),
    ]
