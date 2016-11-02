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
            name='StaffEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start', models.DateTimeField(verbose_name=b'\xe5\xbc\x80\xe5\xa7\x8b\xe6\x97\xa5\xe6\x9c\x9f')),
                ('end', models.DateTimeField(null=True, verbose_name=b'\xe7\xbb\x93\xe6\x9d\x9f\xe6\x97\xa5\xe6\x9c\x9f', blank=True)),
                ('interval_day', models.IntegerField(default=0, verbose_name=b'\xe9\x97\xb4\xe9\x9a\x94\xe5\xa4\xa9\xe6\x95\xb0')),
                ('title', models.CharField(max_length=1000, verbose_name=b'\xe5\x86\x85\xe5\xae\xb9', blank=True)),
                ('type', models.CharField(blank=True, max_length=1000, verbose_name=b'\xe7\xb1\xbb\xe5\x9e\x8b', choices=[(b'peroid', '\u5468\u671f\u4efb\u52a1'), (b'temp', '\u4e00\u6b21\u4efb\u52a1')])),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xa5\xe6\x9c\x9f', null=True)),
                ('is_finished', models.BooleanField(default=False, verbose_name=b'\xe5\xb7\xb2\xe5\xae\x8c\xe6\x88\x90')),
                ('status', models.CharField(default=b'normal', max_length=10, verbose_name=b'\xe7\x8a\xb6\xe6\x80\x81', choices=[(b'normal', '\u6b63\u5e38'), (b'cancel', '\u53d6\u6d88')])),
                ('creator', models.ForeignKey(related_name='staff_create_events', default=None, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe8\x80\x85', to=settings.AUTH_USER_MODEL, null=True)),
                ('executor', models.ForeignKey(related_name='staff_execute_events', default=None, verbose_name=b'\xe6\x89\xa7\xe8\xa1\x8c\xe8\x80\x85', to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'shop_calendar_staffevent',
                'verbose_name': '\u4e8b\u4ef6',
                'verbose_name_plural': '\u4e8b\u4ef6\u5217\u8868',
            },
        ),
    ]
