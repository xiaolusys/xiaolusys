# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WeixinBomb',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64, verbose_name='\u5fae\u4fe1\u53f7', blank=True)),
                ('contact', models.CharField(max_length=32, verbose_name='\u8054\u7cfb\u4eba', blank=True)),
                ('phone', models.CharField(max_length=32, verbose_name='\u7535\u8bdd', blank=True)),
                ('mobile', models.CharField(max_length=16, verbose_name='\u624b\u673a', blank=True)),
                ('email', models.CharField(max_length=64, verbose_name='\u90ae\u7bb1', blank=True)),
                ('qq', models.CharField(max_length=16, verbose_name='QQ\u53f7', blank=True)),
                ('numfans', models.IntegerField(default=0, verbose_name=b'\xe7\xb2\x89\xe4\xb8\x9d\xe6\x95\xb0')),
                ('region', models.CharField(max_length=16, verbose_name='\u5730\u533a', blank=True)),
                ('category', models.CharField(max_length=16, verbose_name='\u7c7b\u522b', blank=True)),
                ('price', models.IntegerField(default=0, verbose_name='\u6807\u6ce8\u4ef7')),
                ('coverage', models.IntegerField(default=0, verbose_name='\u8986\u76d6\u4f30\u8ba1')),
                ('payinfo', models.CharField(max_length=128, verbose_name='\u652f\u4ed8\u4fe1\u606f', blank=True)),
                ('memo', models.TextField(verbose_name='\u5907\u6ce8', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('creator', models.ForeignKey(related_name='bombers', verbose_name='\u63a5\u6d3d\u4eba', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'games_bomb_weixinbomb',
                'verbose_name': '\u5fae\u4fe1bomb',
                'verbose_name_plural': '\u5fae\u4fe1bomb\u5217\u8868',
            },
        ),
    ]
