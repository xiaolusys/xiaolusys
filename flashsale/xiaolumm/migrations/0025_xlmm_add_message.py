# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0024_auto_20160730_1816'),
    ]

    operations = [
        migrations.CreateModel(
            name='XlmmMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('title', models.CharField(max_length=500, verbose_name='\u6d88\u606f\u6807\u9898')),
                ('content_link', models.CharField(help_text='\u4f18\u5148\u4f7f\u7528\u6d88\u606f\u94fe\u63a5', max_length=512, null=True, verbose_name='\u5185\u5bb9\u94fe\u63a5', blank=True)),
                ('content', models.CharField(max_length=512, verbose_name='\u6d88\u606f\u5185\u5bb9', blank=True)),
                ('dest', models.CharField(help_text='null\u8868\u793a\u53d1\u7ed9\u4e86\u6240\u6709\u5c0f\u9e7f\u5988\u5988;\u5426\u5219\u586b\u5199django orm\u67e5\u8be2\u6761\u4ef6\u5b57\u5178json', max_length=10000, null=True, verbose_name='\u63a5\u6536\u4eba')),
                ('status', models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u65e0\u6548'), (1, '\u6709\u6548')])),
            ],
            options={
                'db_table': 'xiaolumm_message',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6d88\u606f',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6d88\u606f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='XlmmMessageRel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('read', models.BooleanField(default=True, verbose_name='\u72b6\u6001')),
                ('mama', models.ForeignKey(verbose_name='\u63a5\u53d7\u8005', to='xiaolumm.XiaoluMama')),
                ('message', models.ForeignKey(to='xiaolumm.XlmmMessage')),
            ],
            options={
                'db_table': 'xiaolumm_message_rel',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u4e2a\u4eba\u6d88\u606f\u72b6\u6001',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u4e2a\u4eba\u6d88\u606f\u72b6\u6001\u5217\u8868',
            },
        )
    ]
