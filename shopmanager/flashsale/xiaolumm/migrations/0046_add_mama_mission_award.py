# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0045_add_field_cashout_cash_out_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaMission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u4efb\u52a1\u540d\u79f0')),
                ('target', models.CharField(default=b'personal', max_length=8, verbose_name='\u4efb\u52a1\u5bf9\u8c61', choices=[(b'personal', '\u4e2a\u4eba'), (b'group', '\u56e2\u961f')])),
                ('kpi_type', models.CharField(default=b'count', max_length=8, verbose_name='\u8003\u6838\u65b9\u5f0f', choices=[(b'count', '\u8ba1\u6570'), (b'amount', '\u91d1\u989d')])),
                ('target_value', models.IntegerField(default=0, verbose_name='\u4efb\u52a1\u8fbe\u6807\u6570')),
                ('award_amount', models.IntegerField(default=0, verbose_name='\u8fbe\u6807\u5956\u52b1(\u5206)')),
                ('start_time', models.DateTimeField(null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True)),
                ('date_type', models.CharField(default=b'weekly', max_length=8, verbose_name='\u4efb\u52a1\u5468\u671f', choices=[(b'weekly', '\u5468\u4efb\u52a1'), (b'monthly', '\u6708\u4efb\u52a1'), (b'deadline', 'DEADLINE')])),
                ('status', models.CharField(default=b'draft', max_length=8, verbose_name='\u72b6\u6001', choices=[(b'draft', '\u8349\u7a3f'), (b'progress', '\u8fdb\u884c\u4e2d'), (b'finished', '\u5df2\u7ed3\u675f'), (b'cancel', '\u5df2\u53d6\u6d88')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_mission',
                'verbose_name': 'V2/\u5988\u5988\u6fc0\u52b1\u4efb\u52a1',
                'verbose_name_plural': 'V2/\u5988\u5988\u6fc0\u52b1\u4efb\u52a1\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='MamaMissionRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(default=0, verbose_name='\u5988\u5988id')),
                ('referal_from_mama_id', models.IntegerField(default=0, verbose_name='\u63a8\u8350\u4ebaid', db_index=True)),
                ('group_leader_mama_id', models.IntegerField(default=0, verbose_name='\u56e2\u961f\u961f\u957fid', db_index=True)),
                ('year_week', models.CharField(db_index=True, max_length=16, verbose_name='\u5e74-\u5468', blank=True)),
                ('finish_value', models.IntegerField(default=0, verbose_name='\u5b8c\u6210\u503c')),
                ('finish_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u5b8c\u6210\u65f6\u95f4', blank=True)),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00\u7ea6\u675f')),
                ('status', models.CharField(default=b'staging', max_length=8, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'staging', '\u8fdb\u884c\u4e2d'), (b'finished', '\u5df2\u5b8c\u6210'), (b'close', '\u672a\u5b8c\u6210')])),
                ('mission', models.ForeignKey(verbose_name='\u5173\u8054\u4efb\u52a1', to='xiaolumm.MamaMission')),
            ],
            options={
                'db_table': 'flashsale_xlmm_missionrecord',
                'verbose_name': 'V2/\u5988\u5988\u6fc0\u52b1\u4efb\u52a1\u8bb0\u5f55',
                'verbose_name_plural': 'V2/\u5988\u5988\u6fc0\u52b1\u4efb\u52a1\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.DeleteModel(
            name='MamaWeeklyAward',
        ),
        migrations.AlterIndexTogether(
            name='mamamissionrecord',
            index_together=set([('mama_id', 'year_week', 'mission')]),
        ),
    ]
