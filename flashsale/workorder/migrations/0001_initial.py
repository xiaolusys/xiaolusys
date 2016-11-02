# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='\u5de5\u5355\u7f16\u53f7', primary_key=True)),
                ('problem_title', models.TextField(max_length=32, verbose_name='\u95ee\u9898\u6807\u9898', blank=True)),
                ('problem_type', models.IntegerField(blank=True, verbose_name='\u95ee\u9898\u7c7b\u578b', choices=[(1, '\u82f9\u679c'), (2, '\u5b89\u5353'), (3, '\u5fae\u4fe1\u5546\u57ce'), (4, '\u8d22\u52a1'), (5, '\u91c7\u8d2d'), (6, '\u4f9b\u5e94\u94fe'), (7, '\u4ed3\u5e93')])),
                ('problem_desc', models.TextField(max_length=1024, verbose_name='\u95ee\u9898\u63cf\u8ff0', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u5de5\u5355\u5904\u7406\u72b6\u6001', choices=[(0, '\u5f85\u5904\u7406'), (1, '\u5904\u7406\u4e2d'), (2, '\u5df2\u5904\u7406'), (3, '\u5df2\u5b8c\u6210')])),
                ('is_valid', models.IntegerField(default=1, verbose_name='\u5de5\u5355\u72b6\u6001', choices=[(1, '\u6709\u6548'), (0, '\u65e0\u6548')])),
                ('level', models.IntegerField(default=2, verbose_name='\u5de5\u5355\u7b49\u7ea7', choices=[(1, '\u4e25\u91cd'), (2, '\u666e\u901a'), (3, '\u8f7b\u5fae')])),
                ('problem_back', models.TextField(max_length=1024, verbose_name='\u95ee\u9898\u53cd\u9988', blank=True)),
                ('creater', models.CharField(db_index=True, max_length=32, verbose_name='\u521b\u5efa\u4eba', blank=True)),
                ('dealer', models.CharField(db_index=True, max_length=32, verbose_name='\u5904\u7406\u4eba', blank=True)),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='\u63d0\u4ea4\u65e5\u671f', db_index=True)),
                ('modified_time', models.DateTimeField(null=True, verbose_name='\u5904\u7406\u65e5\u671f', db_index=True)),
            ],
            options={
                'db_table': 'flashsale_workorder',
                'verbose_name': '\u5de5\u5355',
                'verbose_name_plural': '\u5de5\u5355\u5217\u8868',
            },
        ),
    ]
