# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0017_add_start_time_end_time_to_rebeta_plan'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarryTotalRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('stat_time', models.DateTimeField(verbose_name='\u7edf\u8ba1\u65f6\u95f4')),
                ('total_rank', models.IntegerField(default=0, verbose_name='\u603b\u989d\u6392\u540d')),
                ('duration_rank', models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u671f\u95f4\u6392\u540d')),
                ('history_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u5386\u53f2\u6536\u76ca\u603b\u989d')),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('history_num', models.IntegerField(default=0, verbose_name='\u56e2\u961f\u8ba2\u5355\u6570\u91cf', db_index=True)),
                ('duration_num', models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u671f\u95f4\u56e2\u961f\u8ba2\u5355\u6570\u91cf')),
                ('carry_records', jsonfield.fields.JSONField(default=b'[]', max_length=10240, verbose_name='\u6bcf\u65e5\u6536\u76ca\u5173\u8054', blank=True)),
            ],
            options={
                'db_table': 'xiaolumm_carry_total_record',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d\u8bb0\u5f55',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d\u8bb0\u5f55',
            },
        ),
        migrations.CreateModel(
            name='MamaCarryTotal',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama', models.OneToOneField(primary_key=True, serialize=False, to='xiaolumm.XiaoluMama')),
                ('history_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u5386\u53f2\u6536\u76ca\u603b\u989d')),
                ('stat_time', models.DateTimeField(default=datetime.datetime(2016, 7, 20, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4')),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('history_num', models.IntegerField(default=0, verbose_name='\u56e2\u961f\u8ba2\u5355\u6570\u91cf', db_index=True)),
                ('duration_num', models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u671f\u95f4\u56e2\u961f\u8ba2\u5355\u6570\u91cf')),
                ('carry_records', jsonfield.fields.JSONField(default=b'[]', max_length=10240, verbose_name='\u6bcf\u65e5\u6536\u76ca\u5173\u8054', blank=True)),
                ('total_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206,\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u603b\u6392\u540d')),
                ('duration_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d')),
            ],
            options={
                'db_table': 'xiaolumm_carry_total',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='MamaTeamCarryTotal',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama', models.OneToOneField(primary_key=True, serialize=False, to='xiaolumm.XiaoluMama')),
                ('total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u56e2\u961f\u6536\u76ca\u603b\u989d')),
                ('num', models.IntegerField(default=0, verbose_name='\u56e2\u961f\u8ba2\u5355\u6570\u91cf')),
                ('duration_num', models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u671f\u95f4\u56e2\u961f\u8ba2\u5355\u6570\u91cf')),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('stat_time', models.DateTimeField(default=datetime.datetime(2016, 7, 20, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4')),
                ('total_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206,\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u603b\u6392\u540d')),
                ('duration_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d')),
                ('members', models.ManyToManyField(related_name='teams', to='xiaolumm.MamaCarryTotal')),
            ],
            options={
                'db_table': 'xiaolumm_team_carry_total',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u56e2\u961f\u6536\u76ca\u6392\u540d',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u56e2\u961f\u6536\u76ca\u6392\u540d\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='TeamCarryTotalRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('stat_time', models.DateTimeField(default=datetime.datetime(2016, 7, 20, 0, 0), verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4')),
                ('total_rank', models.IntegerField(default=0, verbose_name='\u603b\u989d\u6392\u540d')),
                ('duration_rank', models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u671f\u95f4\u6392\u540d')),
                ('total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u56e2\u961f\u6536\u76ca\u603b\u989d')),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('num', models.IntegerField(default=0, verbose_name='\u56e2\u961f\u8ba2\u5355\u6570\u91cf', db_index=True)),
                ('duration_num', models.IntegerField(default=0, verbose_name='\u6d3b\u52a8\u671f\u95f4\u56e2\u961f\u8ba2\u5355\u6570\u91cf')),
                ('mama_ids', jsonfield.fields.JSONField(default=b'[]', max_length=10240, verbose_name='\u76f8\u5173\u5988\u5988', blank=True)),
            ],
            options={
                'db_table': 'xiaolumm_team_carry_total_record',
                'verbose_name': '\u5988\u5988\u56e2\u961f\u6536\u76ca\u6392\u540d\u8bb0\u5f55',
                'verbose_name_plural': '\u5988\u5988\u56e2\u961f\u6536\u76ca\u6392\u540d\u8bb0\u5f55',
            },
        ),
        migrations.AlterField(
            model_name='agencyorderrebetascheme',
            name='start_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='referal_from',
            field=models.CharField(help_text='\u5988\u5988\u7684id', max_length=11, verbose_name='\u63a8\u8350\u4eba', db_index=True, blank=True),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='mama',
            field=models.ForeignKey(to='xiaolumm.XiaoluMama'),
        ),
        migrations.AddField(
            model_name='carrytotalrecord',
            name='mama',
            field=models.ForeignKey(to='xiaolumm.XiaoluMama'),
        ),
    ]
