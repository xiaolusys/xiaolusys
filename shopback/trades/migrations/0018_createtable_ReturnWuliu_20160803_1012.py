# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0017_auto_20160629_1717'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReturnWuLiu',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tid', models.CharField(db_index=True, max_length=32, verbose_name='\u539f\u5355ID', blank=True)),
                ('out_sid', models.CharField(db_index=True, max_length=64, verbose_name='\u7269\u6d41\u7f16\u53f7', blank=True)),
                ('logistics_company', models.CharField(db_index=True, max_length=64, verbose_name='\u7269\u6d41\u516c\u53f8', blank=True)),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u7269\u6d41\u72b6\u6001', choices=[(0, '\u67e5\u8be2\u5f02\u5e38'), (1, '\u6ca1\u6709\u8bb0\u5f55'), (2, '\u5728\u8def\u4e0a'), (3, '\u6d3e\u9001\u4e2d'), (4, '\u5df2\u7ecf\u7b7e\u6536'), (5, '\u62d2\u7edd\u7b7e\u6536'), (6, '\u67d0\u4e9b\u539f\u56e0\uff0c\u65e0\u6cd5\u6d3e\u9001'), (7, '\u65e0\u6548\u5355'), (8, '\u8d85\u65f6\u5355'), (9, '\u7b7e\u6536\u5931\u8d25')])),
                ('time', models.DateTimeField(null=True, verbose_name='\u65f6\u95f4', db_index=True)),
                ('content', models.CharField(max_length=640, verbose_name='\u7269\u6d41\u8be6\u60c5', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='\u8bb0\u5f55\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True)),
                ('errcode', models.CharField(max_length=64, verbose_name='\u9519\u8bef\u4ee3\u7801', blank=True)),
                ('remark', models.CharField(max_length=64, verbose_name='\u5907\u6ce8', blank=True)),
                ('icon', models.CharField(max_length=256, verbose_name='\u7269\u6d41\u516c\u53f8\u56fe\u6807', blank=True)),
                ('rid', models.CharField(db_index=True, max_length=32, verbose_name='\u9000\u8d27\u5355ID', blank=True)),
            ],
            options={
                'db_table': 'shop_returns_wuliudetail',
                'verbose_name': '\u9000\u8d27\u7269\u6d41\u8ddf\u8e2a',
                'verbose_name_plural': '\u9000\u8d27\u7269\u6d41\u8ddf\u8e2a\u5217\u8868',
            },
        ),
    ]
