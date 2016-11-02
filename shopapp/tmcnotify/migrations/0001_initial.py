# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TmcMessage',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('user_id', models.BigIntegerField(verbose_name='\u5e97\u94faID', db_index=True)),
                ('topic', models.CharField(max_length=128, verbose_name='\u6d88\u606f\u4e3b\u9898', blank=True)),
                ('pub_app_key', models.CharField(max_length=64, verbose_name='\u53d1\u5e03\u8005APPKEY', blank=True)),
                ('pub_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u53d1\u5e03\u65f6\u95f4', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u5165\u5e93\u65f6\u95f4')),
                ('content', models.TextField(max_length=2000, verbose_name='\u6d88\u606f\u5185\u5bb9', blank=True)),
                ('is_exec', models.BooleanField(default=False, verbose_name='\u6267\u884c')),
            ],
            options={
                'db_table': 'shop_tmcnotify_message',
                'verbose_name': '\u670d\u52a1\u6d88\u606f',
                'verbose_name_plural': '\u670d\u52a1\u6d88\u606f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='TmcUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.BigIntegerField(verbose_name='\u5e97\u94faID', db_index=True)),
                ('user_nick', models.CharField(max_length=64, verbose_name='\u7528\u6237\u6635\u79f0', blank=True)),
                ('modified', models.DateTimeField(null=True, verbose_name='\u4fee\u6539\u65f6\u95f4', blank=True)),
                ('created', models.DateTimeField(null=True, verbose_name='\u521b\u5efa\u65f6\u95f4', blank=True)),
                ('topics', models.TextField(max_length=2500, verbose_name='\u6d88\u606f\u4e3b\u9898', blank=True)),
                ('group_name', models.CharField(default=b'default', max_length=64, verbose_name='\u6d88\u606f\u7fa4\u7ec4', blank=True)),
                ('quantity', models.IntegerField(default=100, verbose_name='\u6d88\u606f\u6570\u91cf')),
                ('is_valid', models.BooleanField(default=False, verbose_name='\u662f\u5426\u6709\u6548')),
                ('is_primary', models.BooleanField(default=False, verbose_name='\u4e3b\u7528\u6237')),
            ],
            options={
                'db_table': 'shop_tmcnotify_user',
                'verbose_name': '\u6d88\u606f\u670d\u52a1\u7528\u6237',
                'verbose_name_plural': '\u6d88\u606f\u670d\u52a1\u7528\u6237\u5217\u8868',
            },
        ),
    ]
