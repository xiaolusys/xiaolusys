# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0005_add_headimg_and_nick'),
    ]

    operations = [
        migrations.CreateModel(
            name='DownloadMobileRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('from_customer', models.IntegerField(verbose_name='\u6765\u81ea\u7528\u6237', db_index=True)),
                ('mobile', models.CharField(max_length=11, verbose_name='\u7528\u6237\u624b\u673a\u53f7', db_index=True)),
                ('ufrom', models.IntegerField(default=0, verbose_name='\u6765\u6e90', choices=[(0, '\u672a\u77e5'), (1, '\u4e8c\u7ef4\u7801'), (2, '\u6d3b\u52a8'), (3, '\u7ea2\u5305')])),
                ('uni_key', models.CharField(unique=True, max_length=64, verbose_name='\u552f\u4e00\u6807\u8bc6')),
            ],
            options={
                'db_table': 'flashsale_promotion_download_mobile_record',
                'verbose_name': '\u63a8\u5e7f/\u4e0b\u8f7d\u624b\u673a\u8bb0\u5f55\u8868',
                'verbose_name_plural': '\u63a8\u5e7f/\u4e0b\u8f7d\u624b\u673a\u8bb0\u5f55\u8868',
            },
        ),
        migrations.CreateModel(
            name='DownloadUnionidRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('from_customer', models.IntegerField(verbose_name='\u6765\u81ea\u7528\u6237', db_index=True)),
                ('ufrom', models.IntegerField(default=0, verbose_name='\u6765\u6e90', choices=[(0, '\u672a\u77e5'), (1, '\u4e8c\u7ef4\u7801'), (2, '\u6d3b\u52a8'), (3, '\u7ea2\u5305')])),
                ('uni_key', models.CharField(unique=True, max_length=64, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('unionid', models.CharField(max_length=64, verbose_name='\u5fae\u4fe1\u6388\u6743unionid', db_index=True)),
                ('headimgurl', models.CharField(max_length=256, verbose_name='\u5934\u56fe', blank=True)),
                ('nick', models.CharField(max_length=32, verbose_name='\u6635\u79f0', blank=True)),
            ],
            options={
                'db_table': 'flashsale_promotion_download_unionid_record',
                'verbose_name': '\u63a8\u5e7f/\u4e0b\u8f7dunionid\u8bb0\u5f55\u8868',
                'verbose_name_plural': '\u63a8\u5e7f/\u4e0b\u8f7dunionid\u8bb0\u5f55\u8868',
            },
        ),
    ]
