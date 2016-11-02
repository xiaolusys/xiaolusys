# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0036_add_device_version_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeekMamaCarryTotal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('last_renew_type', models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')])),
                ('agencylevel', models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')])),
                ('stat_time', models.DateTimeField(verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True)),
                ('total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u6536\u76ca\u603b\u989d')),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('order_num', models.IntegerField(default=0, verbose_name='\u5386\u53f2\u8ba2\u5355\u6570\u91cf', db_index=True)),
                ('total_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206,\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u603b\u6392\u540d', db_index=True)),
                ('duration_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True)),
                ('mama', models.ForeignKey(to='xiaolumm.XiaoluMama')),
            ],
            options={
                'db_table': 'xiaolumm_week_carry_total',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u6536\u76ca\u6392\u540d\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='WeekMamaTeamCarryTotal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('last_renew_type', models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')])),
                ('agencylevel', models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')])),
                ('stat_time', models.DateTimeField(verbose_name='\u7edf\u8ba1\u8d77\u59cb\u65f6\u95f4', db_index=True)),
                ('total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u56e2\u961f\u6536\u76ca\u603b\u989d')),
                ('duration_total', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206', verbose_name='\u7edf\u8ba1\u671f\u95f4\u6536\u76ca\u603b\u989d')),
                ('total_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206,\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u603b\u6392\u540d', db_index=True)),
                ('duration_rank_delay', models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0', verbose_name='\u6d3b\u52a8\u671f\u6392\u540d', db_index=True)),
                ('mama', models.ForeignKey(to='xiaolumm.XiaoluMama')),
                ('members', models.ManyToManyField(related_name='teams', to='xiaolumm.WeekMamaCarryTotal')),
            ],
            options={
                'db_table': 'xiaolumm_week_team_carry_total',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u56e2\u961f\u5468\u6536\u76ca\u6392\u540d',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u56e2\u961f\u5468\u6536\u76ca\u6392\u540d\u5217\u8868',
            },
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u65b0\u624b\u4efb\u52a1'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u63a8\u8350\u65b0\u624b\u4efb\u52a1'), (7, '\u4e00\u5143\u9080\u8bf7')]),
        ),
        migrations.AlterUniqueTogether(
            name='weekmamateamcarrytotal',
            unique_together=set([('mama', 'stat_time')]),
        ),
        migrations.AlterUniqueTogether(
            name='weekmamacarrytotal',
            unique_together=set([('mama', 'stat_time')]),
        ),
    ]
