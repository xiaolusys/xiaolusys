# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0021_add_salerefund_is_lackrefund_and_lackorder_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='DistrictVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('version', models.CharField(unique=True, max_length=32, verbose_name='\u7248\u672c\u53f7')),
                ('download_url', models.CharField(max_length=256, verbose_name='\u4e0b\u8f7d\u94fe\u63a5', blank=True)),
                ('hash256', models.CharField(max_length=b'128', verbose_name='hash256\u503c', blank=True)),
                ('memo', models.TextField(verbose_name='\u5907\u6ce8', blank=True)),
                ('status', models.BooleanField(default=False, verbose_name='\u751f\u6548')),
            ],
            options={
                'db_table': 'flashsale_district_version',
                'verbose_name': '\u5730\u5740/\u533a\u5212\u7248\u672c',
                'verbose_name_plural': '\u5730\u5740/\u533a\u5212\u7248\u672c\u66f4\u65b0\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='district',
            name='is_valid',
            field=models.BooleanField(default=True, verbose_name='\u6709\u6548'),
        ),
        migrations.AddField(
            model_name='district',
            name='zipcode',
            field=models.CharField(max_length=16, verbose_name='\u90ae\u653f\u7f16\u7801', blank=True),
        ),
    ]
