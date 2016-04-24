# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AppRelease',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('download_link', models.CharField(max_length=512, verbose_name='\u5b58\u50a8\u94fe\u63a5\u5730\u5740')),
                ('qrcode_link', models.CharField(max_length=512, verbose_name='\u4e8c\u7ef4\u7801\u94fe\u63a5\u5730\u5740')),
                ('version', models.CharField(max_length=128, verbose_name='\u5ba2\u6237\u7aef\u7248\u672c\u53f7', db_index=True)),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u6295\u653e\u72b6\u6001', choices=[(0, '\u6709\u6548'), (1, '\u65e0\u6548')])),
                ('release_time', models.DateTimeField(null=True, verbose_name='\u6295\u653e\u65f6\u95f4', blank=True)),
                ('memo', models.TextField(max_length=1024, null=True, verbose_name='\u5907\u6ce8', blank=True)),
            ],
            options={
                'db_table': 'flashsale_app_release',
                'verbose_name': '\u7279\u5356/App\u4e0b\u8f7d\u7248\u672c\u8868',
                'verbose_name_plural': '\u7279\u5356/App\u4e0b\u8f7d\u7248\u672c\u5217\u8868',
            },
        ),
    ]
