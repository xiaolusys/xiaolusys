# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PushMsgTpl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u6a21\u677f\u540d\u79f0')),
                ('tpl_content', models.CharField(max_length=128, verbose_name='\u63a8\u9001\u6d88\u606f\u6a21\u677f')),
                ('is_valid', models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u6709\u6548')),
            ],
            options={
                'db_table': 'push_msg_tpl',
                'verbose_name': '\u63a8\u9001/\u63a8\u9001\u4fe1\u606f\u6a21\u677f\u8868',
                'verbose_name_plural': '\u63a8\u9001/\u63a8\u9001\u4fe1\u606f\u6a21\u677f\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PushTopic',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='\u4e3b\u952e', primary_key=True)),
                ('cat', models.PositiveIntegerField(default=0, verbose_name='\u5206\u7c7b', blank=True)),
                ('platform', models.CharField(max_length=16, verbose_name='\u5e73\u53f0')),
                ('regid', models.CharField(max_length=512, verbose_name='\u5c0f\u7c73regid')),
                ('ios_token', models.CharField(max_length=128, verbose_name='ios\u7cfb\u7edftoken', blank=True)),
                ('device_id', models.CharField(max_length=256, verbose_name='\u8bbe\u5907ID', blank=True)),
                ('topic', models.CharField(max_length=128, verbose_name='\u63a8\u9001\u6807\u7b7e', blank=True)),
                ('update_time', models.FloatField(null=True, verbose_name='\u66f4\u65b0\u65f6\u95f4', blank=True)),
                ('status', models.SmallIntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u65e0\u6548'), (1, '\u6709\u6548')])),
                ('customer', models.ForeignKey(verbose_name='\u7528\u6237', blank=True, to='pay.Customer', null=True)),
            ],
            options={
                'db_table': 'push_topics',
                'verbose_name': '\u5c0f\u7c73\u63a8\u9001\u6807\u7b7e',
                'verbose_name_plural': '\u5c0f\u7c73\u63a8\u9001\u6807\u7b7e',
            },
        ),
    ]
