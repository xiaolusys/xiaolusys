# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BabyPhone',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('fa_mobile', models.BigIntegerField(null=True, verbose_name=b'\xe7\x88\xb6\xe4\xba\xb2\xe5\x8f\xb7\xe7\xa0\x81', db_index=True)),
                ('ma_mobile', models.BigIntegerField(null=True, verbose_name=b'\xe6\xaf\x8d\xe4\xba\xb2\xe5\x8f\xb7\xe7\xa0\x81', db_index=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe5\xae\x9d\xe5\xae\x9d\xe5\x90\x8d', blank=True)),
                ('father', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe7\x88\xb6\xe4\xba\xb2\xe5\x90\x8d', blank=True)),
                ('mather', models.CharField(db_index=True, max_length=64, verbose_name=b'\xe6\xaf\x8d\xe4\xba\xb2\xe5\x90\x8d', blank=True)),
                ('state', models.CharField(max_length=32, verbose_name=b'\xe7\x9c\x81', blank=True)),
                ('address', models.CharField(max_length=256, verbose_name=b'\xe5\x9c\xb0\xe5\x9d\x80', blank=True)),
                ('sex', models.CharField(max_length=3, verbose_name=b'\xe6\x80\xa7\xe5\x88\xab', blank=True)),
                ('born', models.DateField(null=True, verbose_name=b'\xe5\x87\xba\xe7\x94\x9f\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('code', models.CharField(max_length=64, verbose_name=b'\xe9\x82\xae\xe7\xbc\x96', blank=True)),
                ('hospital', models.CharField(max_length=64, verbose_name=b'\xe5\x8c\xbb\xe9\x99\xa2', blank=True)),
            ],
            options={
                'db_table': 'shop_babylist_babyphone',
                'verbose_name': '\u65b0\u751f\u513f\u7ae5\u4fe1\u606f',
                'verbose_name_plural': '\u65b0\u751f\u513f\u7ae5\u4fe1\u606f\u5217\u8868',
            },
        ),
    ]
