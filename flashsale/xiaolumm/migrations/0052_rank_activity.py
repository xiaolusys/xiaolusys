# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.xiaolumm.models.carry_total


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0051_weekmamateamcarrytotal_member_ids'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityMamaCarryTotal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('last_renew_type', models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')])),
                ('agencylevel', models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')])),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('duration_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True)),
                ('activity_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True)),
                ('invite_trial_num', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('invite_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u9080\u8bf7\u6570\u6392\u540d', db_index=True)),
            ],
            options={
                'db_table': 'xiaolumm_activity_carry_total',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6d3b\u52a8\u6536\u76ca\u6392\u540d',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6d3b\u52a8\u6536\u76ca\u6392\u540d\u5217\u8868',
            },
            bases=(models.Model, flashsale.xiaolumm.models.carry_total.ActivityRankTotal),
        ),
        migrations.CreateModel(
            name='RankActivity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('start_time', models.DateField(verbose_name='\u6d3b\u52a8\u5f00\u59cb\u65f6\u95f4')),
                ('end_time', models.DateField(verbose_name='\u6d3b\u52a8\u7ed3\u675f\u65f6\u95f4')),
                ('status', models.IntegerField(default=1, verbose_name='\u72b6\u6001')),
                ('note', models.CharField(max_length=100, verbose_name='\u5907\u6ce8')),
            ],
            options={
                'db_table': 'xiaolumm_rank_activity',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d\u6d3b\u52a8',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d\u6d3b\u52a8\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='activitymamacarrytotal',
            name='activity',
            field=models.ForeignKey(related_name='ranks', verbose_name='\u6d3b\u52a8', to='xiaolumm.RankActivity'),
        ),
        migrations.AddField(
            model_name='activitymamacarrytotal',
            name='mama',
            field=models.ForeignKey(to='xiaolumm.XiaoluMama'),
        ),
        migrations.AlterUniqueTogether(
            name='activitymamacarrytotal',
            unique_together=set([('mama', 'activity')]),
        ),
        migrations.CreateModel(
            name='ActivityMamaTeamCarryTotal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('last_renew_type', models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')])),
                ('agencylevel', models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')])),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('duration_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True)),
                ('activity_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True)),
            ],
            options={
                'db_table': 'xiaolumm_activity_team_carry_total',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6d3b\u52a8\u6536\u76ca\u6392\u540d',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6d3b\u52a8\u6536\u76ca\u6392\u540d\u5217\u8868',
            },
            bases=(models.Model, flashsale.xiaolumm.models.carry_total.ActivityRankTotal),
        ),
        migrations.AddField(
            model_name='activitymamateamcarrytotal',
            name='activity',
            field=models.ForeignKey(related_name='teamranks', verbose_name='\u6d3b\u52a8', to='xiaolumm.RankActivity'),
        ),
        migrations.AddField(
            model_name='activitymamateamcarrytotal',
            name='mama',
            field=models.ForeignKey(to='xiaolumm.XiaoluMama'),
        ),
        migrations.AlterUniqueTogether(
            name='activitymamateamcarrytotal',
            unique_together=set([('mama', 'activity')]),
        ),
    ]
