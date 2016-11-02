# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import jsonfield
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0059_weixinpushevent'),
    ]

    operations = [
        migrations.CreateModel(
            name='XlmmEffectScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(unique=True, null=True, db_index=True)),
                ('score', models.IntegerField(default=0, verbose_name='\u8bc4\u5206')),
                ('stat_time', models.DateTimeField(verbose_name='\u7edf\u8ba1\u65f6\u95f4')),
            ],
            options={
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u771f\u5b9e\u6027\u4e2a\u4eba\u8bc4\u5206',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u771f\u5b9e\u6027\u4e2a\u4eba\u8bc4\u5206\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='XlmmTeamEffScore',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(unique=True, null=True, db_index=True)),
                ('member_ids', jsonfield.fields.JSONField(default={}, max_length=5120, verbose_name='\u6d3b\u52a8\u6570\u636e', blank=True)),
                ('score', models.IntegerField(default=0, verbose_name='\u8bc4\u5206')),
                ('stat_time', models.DateTimeField(verbose_name='\u7edf\u8ba1\u65f6\u95f4')),
            ],
            options={
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u771f\u5b9e\u6027\u56e2\u961f\u8bc4\u5206',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u771f\u5b9e\u6027\u56e2\u961f\u8bc4\u5206\u5217\u8868',
            },
        ),
    ]
