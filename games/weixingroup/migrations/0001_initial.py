# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=100)),
                ('begin_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('content', models.CharField(help_text='\u8be6\u7ec6\u4ecb\u7ecd\u8bf4\u660e', max_length=1000, verbose_name='\u6d3b\u52a8\u5185\u5bb9')),
                ('desc', models.CharField(help_text='\u53ef\u80fd\u5c55\u73b0\u7ed9\u7528\u6237\u7684\u63cf\u8ff0', max_length=500, verbose_name='\u63cf\u8ff0')),
                ('note', models.CharField(help_text='\u5c55\u793a\u7ed9\u666e\u901a\u7528\u6237\u7684\u8bf4\u660e', max_length=200, verbose_name='\u5907\u6ce8')),
                ('homepage', models.CharField(max_length=512, verbose_name='\u6d3b\u52a8\u4e3b\u9875')),
                ('pages', jsonfield.fields.JSONField(help_text='\u5197\u4f59\u7684\u8ba2\u8d27\u5355\u5173\u8054', max_length=10240, null=True, verbose_name='\u76f8\u5173\u9875\u9762')),
                ('status', models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u6709\u6548'), (2, '\u4f5c\u5e9f')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ActivityUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('user_id', models.IntegerField()),
                ('activity', models.ForeignKey(to='weixingroup.Activity')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupFans',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('user_id', models.IntegerField(null=True, verbose_name='\u5173\u8054\u7528\u6237')),
                ('head_img_url', models.CharField(max_length=100, verbose_name='\u7528\u6237\u5fae\u4fe1\u5934\u50cf')),
                ('nick', models.CharField(max_length=100, verbose_name='\u7528\u6237\u5fae\u4fe1\u6635\u79f0')),
                ('union_id', models.CharField(max_length=100, verbose_name='\u7528\u6237\u5fae\u4fe1unionid')),
                ('open_id', models.CharField(max_length=100, verbose_name='\u7528\u6237\u5fae\u4fe1openid')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GroupMamaAdministrator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(verbose_name='\u5988\u5988\u7528\u6237id')),
                ('status', models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u6709\u6548'), (2, '\u4f5c\u5e9f')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='XiaoluAdministrator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('user_id', models.IntegerField(verbose_name='\u5173\u8054\u7528\u6237')),
                ('username', models.IntegerField(verbose_name='\u7ba1\u7406\u5458\u7528\u6237\u540d')),
                ('nick', models.IntegerField(verbose_name='\u7ba1\u7406\u5458\u6635\u79f0')),
                ('weixin_qr_img', models.CharField(max_length=255, verbose_name='\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801')),
                ('status', models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u521d\u59cb'), (1, '\u6709\u6548'), (2, '\u4f5c\u5e9f')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='groupmamaadministrator',
            name='admin',
            field=models.ForeignKey(related_name='mama_groups', verbose_name='\u7ba1\u7406\u5458id', to='weixingroup.XiaoluAdministrator'),
        ),
        migrations.AddField(
            model_name='groupfans',
            name='group',
            field=models.ForeignKey(to='weixingroup.GroupMamaAdministrator'),
        ),
    ]
