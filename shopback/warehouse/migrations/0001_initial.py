# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WareHouse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ware_name', models.CharField(max_length=32, verbose_name=b'\xe4\xbb\x93\xe5\xba\x93\xe5\x90\x8d', blank=True)),
                ('city', models.CharField(max_length=32, verbose_name=b'\xe6\x89\x80\xe5\x9c\xa8\xe5\x9f\x8e\xe5\xb8\x82', blank=True)),
                ('address', models.TextField(max_length=256, verbose_name=b'\xe8\xaf\xa6\xe7\xbb\x86\xe5\x9c\xb0\xe5\x9d\x80', blank=True)),
                ('in_active', models.BooleanField(default=True, verbose_name=b'\xe6\x9c\x89\xe6\x95\x88')),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_ware_house',
                'verbose_name': '\u4ed3\u5e93',
                'verbose_name_plural': '\u4ed3\u5e93\u5217\u8868',
            },
        ),
    ]
