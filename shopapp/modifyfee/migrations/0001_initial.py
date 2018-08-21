# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FeeRule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('payment', models.FloatField(verbose_name=b'\xe4\xba\xa4\xe6\x98\x93\xe9\x87\x91\xe9\xa2\x9d')),
                ('discount', models.FloatField(default=1, verbose_name=b'\xe9\x82\xae\xe8\xb4\xb9\xe6\x8a\x98\xe6\x89\xa3')),
                ('adjust_fee', models.FloatField(null=True, verbose_name=b'\xe9\x82\xae\xe8\xb4\xb9\xe8\xb0\x83\xe6\x95\xb4\xe9\x87\x91\xe9\xa2\x9d')),
            ],
            options={
                'db_table': 'shop_modifyfee_feerule',
                'verbose_name': '\u90ae\u8d39\u89c4\u5219',
                'verbose_name_plural': '\u90ae\u8d39\u89c4\u5219\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='ModifyFee',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('tid', models.BigIntegerField(verbose_name=b'\xe6\xb7\x98\xe5\xae\x9d\xe4\xba\xa4\xe6\x98\x93ID')),
                ('buyer_nick', models.CharField(max_length=32, verbose_name=b'\xe4\xb9\xb0\xe5\xae\xb6\xe6\x98\xb5\xe7\xa7\xb0')),
                ('total_fee', models.CharField(max_length=10, verbose_name=b'\xe8\xae\xa2\xe5\x8d\x95\xe9\x87\x91\xe9\xa2\x9d')),
                ('payment', models.CharField(max_length=10, verbose_name=b'\xe5\xae\x9e\xe4\xbb\x98\xe9\x87\x91\xe9\xa2\x9d')),
                ('post_fee', models.CharField(max_length=10, verbose_name=b'\xe5\xae\x9e\xe4\xbb\x98\xe9\x82\xae\xe8\xb4\xb9')),
                ('modify_fee', models.CharField(max_length=10, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe9\x82\xae\xe8\xb4\xb9')),
                ('modified', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'shop_modifyfee_modifyfee',
                'verbose_name': '\u90ae\u8d39\u4fee\u6539\u8bb0\u5f55',
                'verbose_name_plural': '\u90ae\u8d39\u4fee\u6539\u8bb0\u5f55\u5217\u8868',
            },
        ),
    ]
