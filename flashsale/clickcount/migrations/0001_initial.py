# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ClickCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('linkid', models.IntegerField(verbose_name='\u94fe\u63a5ID', db_index=True)),
                ('weikefu', models.CharField(db_index=True, max_length=32, verbose_name='\u5fae\u5ba2\u670d', blank=True)),
                ('agencylevel', models.IntegerField(default=1, verbose_name='\u7c7b\u522b')),
                ('mobile', models.CharField(max_length=11, verbose_name='\u624b\u673a')),
                ('user_num', models.IntegerField(default=0, verbose_name='\u4eba\u6570')),
                ('valid_num', models.IntegerField(default=0, verbose_name='\u6709\u6548\u70b9\u51fb\u4eba\u6570')),
                ('click_num', models.IntegerField(default=0, verbose_name='\u6b21\u6570')),
                ('date', models.DateField(verbose_name='\u65e5\u671f', db_index=True)),
                ('write_time', models.DateTimeField(auto_now_add=True, verbose_name='\u5199\u5165\u65f6\u95f4')),
                ('username', models.IntegerField(default=0, verbose_name='\u63a5\u7ba1\u4eba', db_index=True)),
            ],
            options={
                'ordering': ['-date'],
                'verbose_name_plural': '\u70b9\u51fb\u7edf\u8ba1\u8868\u5217\u8868',
                'db_table': 'flashsale_clickcount',
                'verbose_name': '\u70b9\u51fb\u7edf\u8ba1\u8868',
                'permissions': [('browser_xlmm_active', '\u6d4f\u89c8\u4ee3\u7406\u6d3b\u8dc3\u5ea6')],
            },
        ),
        migrations.CreateModel(
            name='Clicks',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('linkid', models.IntegerField(default=0, verbose_name='\u94fe\u63a5ID', db_index=True)),
                ('openid', models.CharField(db_index=True, max_length=28, verbose_name='OpenId', blank=True)),
                ('app_key', models.CharField(max_length=20, verbose_name='APP KEY', blank=True)),
                ('isvalid', models.BooleanField(default=False, verbose_name=b'\xe6\x98\xaf\xe5\x90\xa6\xe6\x9c\x89\xe6\x95\x88')),
                ('click_time', models.DateTimeField(verbose_name='\u70b9\u51fb\u65f6\u95f4', db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
            ],
            options={
                'db_table': 'xiaolumm_clicks',
                'verbose_name': '\u7528\u6237\u70b9\u51fb\u8bb0\u5f55',
                'verbose_name_plural': '\u7528\u6237\u70b9\u51fb\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='UserClicks',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('unionid', models.CharField(unique=True, max_length=64, verbose_name='UnionID')),
                ('visit_days', models.IntegerField(default=0, verbose_name='\u6d3b\u8dc3\u5929\u6570', db_index=True)),
                ('click_start_time', models.DateTimeField(null=True, verbose_name='\u9996\u6b21\u70b9\u51fb\u65f6\u95f4', db_index=True)),
                ('click_end_time', models.DateTimeField(null=True, verbose_name='\u6700\u540e\u70b9\u51fb\u65f6\u95f4', db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
            ],
            options={
                'db_table': 'flashsale_userclicks',
                'verbose_name': '\u7528\u6237\u6d3b\u8dc3\u8bb0\u5f55',
                'verbose_name_plural': '\u7528\u6237\u6d3b\u8dc3\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='WeekCount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('linkid', models.IntegerField(verbose_name='\u94fe\u63a5ID', db_index=True)),
                ('weikefu', models.CharField(db_index=True, max_length=32, verbose_name='\u5fae\u5ba2\u670d', blank=True)),
                ('user_num', models.IntegerField(default=0, verbose_name='\u70b9\u51fb\u4eba\u6570')),
                ('valid_num', models.IntegerField(default=0, verbose_name='\u6709\u6548\u70b9\u51fb\u6570')),
                ('buyercount', models.IntegerField(default=0, verbose_name='\u8d2d\u4e70\u4eba\u6570')),
                ('ordernumcount', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u603b\u6570')),
                ('conversion_rate', models.FloatField(default=0, verbose_name='\u8f6c\u5316\u7387')),
                ('week_code', models.CharField(max_length=6, verbose_name='\u5468\u7f16\u7801')),
                ('write_time', models.DateTimeField(auto_now_add=True, verbose_name='\u5199\u5165\u65f6\u95f4')),
            ],
            options={
                'ordering': ['write_time'],
                'db_table': 'flashsale_weekcount_table',
                'verbose_name': '\u4ee3\u7406\u8f6c\u5316\u7387\u5468\u7edf\u8ba1',
                'verbose_name_plural': '\u4ee3\u7406\u8f6c\u5316\u7387\u5468\u7edf\u8ba1\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='weekcount',
            unique_together=set([('linkid', 'week_code')]),
        ),
        migrations.AlterUniqueTogether(
            name='clickcount',
            unique_together=set([('linkid', 'date')]),
        ),
    ]
