# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0022_add_catpic_grade_status_to_salecategory'),
    ]

    operations = [
        migrations.CreateModel(
            name='SaleCategoryVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('version', models.CharField(unique=True, max_length=32, verbose_name='\u7248\u672c\u53f7')),
                ('download_url', models.CharField(max_length=256, verbose_name='\u4e0b\u8f7d\u94fe\u63a5', blank=True)),
                ('sha1', models.CharField(max_length=b'128', verbose_name='sha1\u503c', blank=True)),
                ('memo', models.TextField(verbose_name='\u5907\u6ce8', blank=True)),
                ('status', models.BooleanField(default=False, verbose_name='\u751f\u6548')),
            ],
            options={
                'db_table': 'supplychain_salecategory_version',
                'verbose_name': '\u7279\u5356\u7c7b\u76ee\u7248\u672c',
                'verbose_name_plural': '\u7279\u5356\u7c7b\u76ee\u7248\u672c\u66f4\u65b0\u5217\u8868',
            },
        ),
    ]
