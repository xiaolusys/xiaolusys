# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0004_auto_20160713_2022'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('join_user_cnt', models.IntegerField(default=0, verbose_name='\u5fae\u4fe1\u7fa4\u53c2\u4e0e\u7528\u6237\u8ba1\u6570')),
                ('active_user_cnt', models.IntegerField(default=0, verbose_name='\u672c\u6b21\u6d3b\u52a8\u6fc0\u6d3b\u7528\u6237\u8ba1\u6570')),
                ('activity', models.ForeignKey(to='pay.ActivityEntry')),
            ],
            options={
                'verbose_name': '\u5fae\u4fe1\u6d3b\u52a8\u53c2\u4e0e\u7528\u6237\u7edf\u8ba1',
                'verbose_name_plural': '\u5fae\u4fe1\u6d3b\u52a8\u53c2\u4e0e\u7528\u6237\u7edf\u8ba1\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='groupmamaadministrator',
            name='group_uni_key',
            field=models.CharField(default=None, max_length=128, unique=True, null=True, verbose_name='\u5fae\u4fe1\u7fa4\u7f16\u53f7'),
        ),
        migrations.AddField(
            model_name='xiaoluadministrator',
            name='head_img_url',
            field=models.CharField(default=None, max_length=256, null=True, verbose_name='\u7ba1\u7406\u5458\u5934\u50cf'),
        ),
        migrations.AlterField(
            model_name='xiaoluadministrator',
            name='nick',
            field=models.IntegerField(default=None, null=True, verbose_name='\u7ba1\u7406\u5458\u6635\u79f0'),
        ),
        migrations.AlterUniqueTogether(
            name='activityusers',
            unique_together=set([('activity', 'user_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupmamaadministrator',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='activitystat',
            name='group',
            field=models.ForeignKey(related_name='group', to='weixingroup.GroupMamaAdministrator'),
        ),
    ]
