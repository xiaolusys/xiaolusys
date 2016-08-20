# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0043_add_renewtype_extra_in_potential'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaWeeklyAward',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(default=0, verbose_name='\u5988\u5988id', db_index=True)),
                ('referal_from_mama_id', models.IntegerField(default=0, verbose_name='\u63a8\u8350\u4ebaid', db_index=True)),
                ('group_leader_mama_id', models.IntegerField(default=0, verbose_name='\u56e2\u961f\u961f\u957fid', db_index=True)),
                ('week_field', models.CharField(unique=True, max_length=32, verbose_name='week_id', blank=True)),
                ('target_num', models.IntegerField(default=0, verbose_name='\u76ee\u6807\u6570')),
                ('finish_num', models.IntegerField(default=0, verbose_name='\u5b8c\u6210\u6570')),
                ('award_num', models.IntegerField(default=0, verbose_name='\u5956\u91d1')),
                ('category_type', models.IntegerField(default=0, db_index=True, verbose_name='\u5956\u52b1\u9879\u76ee', choices=[(1, '\u9500\u552e\uff08\u4e2a\u4eba\uff09'), (2, '\u9500\u552e\uff08\u56e2\u961f\uff09'), (3, '\u65b0\u589e\u5988\u5988\uff08\u4e0b\u5c5e\uff09'), (4, '\u65b0\u589e\u5988\u5988\uff08\u56e2\u961f\uff09'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u6388\u8bfe\u5956\u91d1'), (7, '\u65b0\u624b\u4efb\u52a1'), (8, '\u65b0\u589e1\u5143\u5988\u5988'), (9, '\u6307\u5bfc\u65b0\u624b\u4efb\u52a1')])),
                ('award_type', models.IntegerField(default=0, db_index=True, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u9500\u552e\u5956\u91d1'), (2, '\u56e2\u961f\u5956\u91d1')])),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('finish_status', models.IntegerField(default=0, db_index=True, verbose_name='\u5b8c\u6210\u72b6\u6001', choices=[(1, '\u5f85\u5b8c\u6210'), (2, '\u5df2\u5b8c\u6210'), (3, '\u672a\u5b8c\u6210')])),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, b'Valid'), (2, b'Invalid')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_mamaweeklyaward',
                'verbose_name': 'V2/\u5988\u5988weekly\u5956\u91d1',
                'verbose_name_plural': 'V2/\u5988\u5988weekly\u5956\u91d1\u5217\u8868',
            },
        ),
    ]
