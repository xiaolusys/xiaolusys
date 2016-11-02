# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='APPFullPushMessge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('desc', models.TextField(max_length=256, verbose_name='\u63a8\u9001\u5185\u5bb9(\u9650200\u5b57)')),
                ('target_url', models.IntegerField(default=1, verbose_name=b'\xe8\xb7\xb3\xe8\xbd\xac\xe9\xa1\xb5\xe9\x9d\xa2', choices=[(1, b'\xe4\xbb\x8a\xe6\x97\xa5\xe4\xb8\x8a\xe6\x96\xb0'), (2, b'\xe6\x98\xa8\xe6\x97\xa5\xe7\x89\xb9\xe5\x8d\x96'), (3, b'\xe6\xbd\xae\xe7\xab\xa5\xe4\xb8\x93\xe5\x8c\xba'), (4, b'\xe6\x97\xb6\xe5\xb0\x9a\xe5\xa5\xb3\xe8\xa3\x85'), (5, b'\xe5\x95\x86\xe5\x93\x81\xe6\xac\xbe\xe5\xbc\x8f\xe9\xa1\xb5'), (6, b'\xe5\x95\x86\xe5\x93\x81\xe8\xaf\xa6\xe6\x83\x85\xe9\xa1\xb5'), (7, b'\xe8\xae\xa2\xe5\x8d\x95\xe8\xaf\xa6\xe6\x83\x85\xe9\xa1\xb5'), (8, b'\xe4\xbc\x98\xe6\x83\xa0\xe5\x88\xb8\xe5\x88\x97\xe8\xa1\xa8'), (9, b'APP\xe6\xb4\xbb\xe5\x8a\xa8\xe9\xa1\xb5'), (10, b'\xe5\xb0\x8f\xe9\xb9\xbf\xe5\xa6\x88\xe5\xa6\x88\xe9\xa6\x96\xe9\xa1\xb5')])),
                ('params', jsonfield.fields.JSONField(default={}, max_length=512, verbose_name='\u63a8\u9001\u53c2\u6570', blank=True)),
                ('cat', models.PositiveIntegerField(default=0, verbose_name='\u5206\u7c7b', blank=True)),
                ('platform', models.CharField(db_index=True, max_length=16, verbose_name='\u5e73\u53f0', choices=[(b'ios', b'\xe5\x85\xa8\xe9\x83\xa8IOS\xe7\x94\xa8\xe6\x88\xb7'), (b'android', b'\xe5\x85\xa8\xe9\x83\xa8ANDROID\xe7\x94\xa8\xe6\x88\xb7')])),
                ('regid', models.CharField(max_length=512, verbose_name='\u5c0f\u7c73regid', blank=True)),
                ('result', jsonfield.fields.JSONField(default={}, max_length=2048, verbose_name='\u63a8\u9001\u7ed3\u679c', blank=True)),
                ('status', models.SmallIntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u5931\u8d25'), (1, '\u751f\u6548')])),
                ('push_time', models.DateTimeField(db_index=True, verbose_name='\u8bbe\u7f6e\u63a8\u9001\u65f6\u95f4', blank=True)),
            ],
            options={
                'db_table': 'flashsale_apppushmsg',
                'verbose_name': '\u7279\u5356/APP\u5168\u7ad9\u63a8\u9001',
                'verbose_name_plural': '\u7279\u5356/APP\u5168\u7ad9\u63a8\u9001',
            },
        ),
    ]
