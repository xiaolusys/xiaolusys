# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='XiaoluSwitch',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('start_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u751f\u6548\u65f6\u95f4', blank=True)),
                ('end_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True)),
                ('responsible', models.CharField(max_length=32, verbose_name='\u8d1f\u8d23\u4eba', db_index=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u6807\u9898', db_index=True)),
                ('description', models.TextField(verbose_name='\u63cf\u8ff0')),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u8bbf\u95ee\u6b21\u6570', choices=[(0, '\u53d6\u6d88'), (1, '\u751f\u6548')])),
            ],
            options={
                'db_table': 'xiaolu_switch',
                'verbose_name': '\u5f00\u5173\u5668',
                'verbose_name_plural': '\u5f00\u5173\u5668\u5217\u8868',
            },
        ),
    ]
