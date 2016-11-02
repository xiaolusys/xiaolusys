# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AttendRecord',
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
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, 'EFFECT'), (1, 'CANCELED')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_attend_record',
                'verbose_name': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u5b66\u5458\u8bb0\u5f55\u8bb0\u5f55',
                'verbose_name_plural': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u5b66\u5458\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=32, verbose_name='\u8bb2\u5e08\u6635\u79f0', blank=True)),
                ('title', models.CharField(max_length=64, verbose_name='\u8bb2\u5e08\u5934\u8854', blank=True)),
                ('image', models.CharField(max_length=256, verbose_name='\u8bb2\u5e08\u5934\u50cf', blank=True)),
                ('introduction', models.TextField(max_length=512, verbose_name='\u8bb2\u5e08\u7b80\u4ecb', blank=True)),
                ('num_lesson', models.IntegerField(default=0, verbose_name='\u603b\u8bfe\u65f6')),
                ('num_attender', models.IntegerField(default=0, verbose_name='\u603b\u542c\u8bfe\u4eba\u6570')),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u6709\u6548'), (1, '\u53d6\u6d88')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_instructor',
                'verbose_name': '\u5c0f\u9e7f\u5927\u5b66/\u8d44\u6df1\u8bb2\u5e08',
                'verbose_name_plural': '\u5c0f\u9e7f\u5927\u5b66/\u8d44\u6df1\u8bb2\u5e08\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('lesson_topic_id', models.IntegerField(default=0, verbose_name='\u8bfe\u7a0b\u4e3b\u9898ID', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u8bfe\u7a0b\u4e3b\u9898', blank=True)),
                ('description', models.TextField(max_length=512, verbose_name='\u8bfe\u7a0b\u63cf\u8ff0', blank=True)),
                ('content_link', models.CharField(max_length=256, verbose_name='\u5185\u5bb9\u94fe\u63a5', blank=True)),
                ('instructor_id', models.IntegerField(default=0, verbose_name='\u8bb2\u5e08ID', db_index=True)),
                ('instructor_name', models.CharField(max_length=32, verbose_name='\u8bb2\u5e08\u6635\u79f0', blank=True)),
                ('instructor_title', models.CharField(max_length=64, verbose_name='\u8bb2\u5e08\u5934\u8854', blank=True)),
                ('instructor_image', models.CharField(max_length=256, verbose_name='\u8bb2\u5e08\u5934\u50cf', blank=True)),
                ('num_attender', models.IntegerField(default=0, verbose_name='\u542c\u8bfe\u4eba\u6570')),
                ('num_score', models.IntegerField(default=0, verbose_name='\u8bfe\u7a0b\u8bc4\u5206')),
                ('start_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('qrcode_links', jsonfield.fields.JSONField(default={}, max_length=1024, verbose_name='\u7fa4\u4e8c\u7ef4\u7801\u94fe\u63a5', blank=True)),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u6709\u6548'), (1, '\u5df2\u5b8c\u6210'), (2, '\u53d6\u6d88')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_lesson',
                'verbose_name': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b',
                'verbose_name_plural': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='LessonTopic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('title', models.CharField(max_length=128, verbose_name='\u8bfe\u7a0b\u4e3b\u9898', blank=True)),
                ('description', models.TextField(max_length=512, verbose_name='\u8bfe\u7a0b\u63cf\u8ff0', blank=True)),
                ('num_attender', models.IntegerField(default=0, verbose_name='\u603b\u542c\u8bfe\u4eba\u6570')),
                ('content_link', models.CharField(max_length=256, verbose_name='\u5185\u5bb9\u94fe\u63a5', blank=True)),
                ('lesson_type', models.IntegerField(default=0, verbose_name='\u7c7b\u578b', choices=[(0, '\u8bfe\u7a0b'), (1, '\u5b9e\u6218'), (2, '\u77e5\u8bc6')])),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u6709\u6548'), (1, '\u53d6\u6d88')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_lesson_topic',
                'verbose_name': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u4e3b\u9898',
                'verbose_name_plural': '\u5c0f\u9e7f\u5927\u5b66/\u8bfe\u7a0b\u4e3b\u9898\u5217\u8868',
            },
        ),
    ]
