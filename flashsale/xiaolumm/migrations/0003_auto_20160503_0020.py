# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0002_attendrecord_instructor_lesson_lessontopic'),
    ]

    operations = [
        migrations.CreateModel(
            name='LessonAttendRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('lesson_id', models.IntegerField(default=0, verbose_name='\u8bfe\u7a0bID', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u8bfe\u7a0b\u4e3b\u9898', blank=True)),
                ('student_unionid', models.CharField(max_length=64, verbose_name='\u5b66\u5458UnionID', db_index=True)),
                ('student_nick', models.CharField(max_length=64, verbose_name='\u5b66\u5458\u6635\u79f0')),
                ('student_image', models.CharField(max_length=256, verbose_name='\u5b66\u5458\u5934\u50cf')),
                ('num_score', models.IntegerField(default=0, verbose_name='\u8bfe\u7a0b\u8bc4\u5206')),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u6709\u6548'), (1, '\u65e0\u6548')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_lesson_attend_record',
                'verbose_name': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u5b66\u5458\u8bb0\u5f55',
                'verbose_name_plural': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u5b66\u5458\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='TopicAttendRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('topic_id', models.IntegerField(default=0, verbose_name='\u4e3b\u9898ID', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u8bfe\u7a0b\u4e3b\u9898', blank=True)),
                ('student_unionid', models.CharField(max_length=64, verbose_name='\u5b66\u5458UnionID', db_index=True)),
                ('student_nick', models.CharField(max_length=64, verbose_name='\u5b66\u5458\u6635\u79f0')),
                ('student_image', models.CharField(max_length=256, verbose_name='\u5b66\u5458\u5934\u50cf')),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('lesson_attend_record_id', models.IntegerField(default=0, verbose_name='\u8bfe\u7a0b\u53c2\u52a0\u8bb0\u5f55ID')),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, 'EFFECT'), (1, 'CANCELED')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_topic_attend_record',
                'verbose_name': '\u5c0f\u9e7f\u5927\u5b66/\u4e3b\u9898\u5b66\u5458\u8bb0\u5f55',
                'verbose_name_plural': '\u5c0f\u9e7f\u5927\u5b66/\u4e3b\u9898\u5b66\u5458\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.DeleteModel(
            name='AttendRecord',
        ),
        migrations.AddField(
            model_name='lesson',
            name='effect_num_attender',
            field=models.IntegerField(default=0, verbose_name='\u6709\u6548\u542c\u8bfe\u4eba\u6570'),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='num_attender',
            field=models.IntegerField(default=0, verbose_name='\u603b\u542c\u8bfe\u4eba\u6570'),
        ),
    ]
