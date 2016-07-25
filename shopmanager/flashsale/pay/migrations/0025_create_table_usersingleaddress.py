# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0024_add_field_extras_salecategory'),
    ]


    operations = [
        migrations.CreateModel(
            name='UserSingleAddress',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('receiver_state', models.CharField(max_length=16, verbose_name='\u7701', blank=True)),
                ('receiver_city', models.CharField(max_length=16, verbose_name='\u5e02', blank=True)),
                ('receiver_district', models.CharField(max_length=16, verbose_name='\u533a', blank=True)),
                ('receiver_address', models.CharField(max_length=128, verbose_name='\u8be6\u7ec6\u5730\u5740', blank=True)),
                ('receiver_zip', models.CharField(max_length=10, verbose_name='\u90ae\u7f16', blank=True)),
                ('uni_key', models.CharField(unique=True, max_length=64, verbose_name=b'\xe5\xae\x8c\xe6\x95\xb4\xe5\x9c\xb0\xe5\x9d\x80\xe5\x94\xaf\xe4\xb8\x80KEY')),
                ('address_hash', models.CharField(db_index=True, max_length=128, verbose_name='\u5730\u5740\u54c8\u5e0c', blank=True)),
                ('note_id', models.IntegerField(default=0, verbose_name=b'\xe5\xae\x8c\xe6\x95\xb4\xe5\x9c\xb0\xe5\x9d\x80ID')),
            ],
            options={
                'db_table': 'flashsale_single_address',
                'verbose_name': '\u7279\u5356\u7528\u6237/\u552f\u4e00\u5730\u5740',
                'verbose_name_plural': '\u7279\u5356\u7528\u6237/\u552f\u4e00\u5730\u5740\u5217\u8868',
            },
        ),
    ]
