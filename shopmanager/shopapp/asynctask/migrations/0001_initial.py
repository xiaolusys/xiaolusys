# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PrintAsyncTaskModel',
            fields=[
                ('task_id', models.AutoField(serialize=False, verbose_name='\u4efb\u52a1ID', primary_key=True)),
                ('task_type', models.IntegerField(default=0, verbose_name='\u4efb\u52a1\u7c7b\u578b', choices=[(0, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe5\x88\x9b\xe5\xbb\xba'), (1, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe5\xae\x8c\xe6\x88\x90'), (-1, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xa4\xb1\xe8\xb4\xa5')])),
                ('operator', models.CharField(db_index=True, max_length=16, verbose_name='\u64cd\u4f5c\u5458', blank=True)),
                ('file_path_to', models.CharField(max_length=256, verbose_name='\u7ed3\u679c\u5b58\u653e\u8def\u5f84', blank=True)),
                ('created', models.DateField(auto_now=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('modified', models.DateField(auto_now_add=True, verbose_name='\u4fee\u6539\u65e5\u671f')),
                ('status', models.IntegerField(default=0, verbose_name='\u4efb\u52a1\u72b6\u6001', choices=[(0, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe5\x88\x9b\xe5\xbb\xba'), (1, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe5\xae\x8c\xe6\x88\x90'), (-1, b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xa4\xb1\xe8\xb4\xa5')])),
                ('params', models.TextField(max_length=5000, null=True, verbose_name='\u4efb\u52a1\u53c2\u6570', blank=True)),
            ],
            options={
                'db_table': 'shop_asynctask_print',
                'verbose_name': '\u5f02\u6b65\u6253\u5370\u4efb\u52a1',
                'verbose_name_plural': '\u5f02\u6b65\u6253\u5370\u4efb\u52a1\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='TaobaoAsyncTaskModel',
            fields=[
                ('task_id', models.AutoField(serialize=False, verbose_name='\u4efb\u52a1ID', primary_key=True)),
                ('task', models.TextField(max_length=256, verbose_name='\u4efb\u52a1\u6807\u9898', blank=True)),
                ('top_task_id', models.CharField(db_index=True, max_length=128, verbose_name='\u6dd8\u5b9d\u4efb\u52a1ID', blank=True)),
                ('user_id', models.CharField(max_length=64, verbose_name='\u7528\u6237ID', blank=True)),
                ('result', models.TextField(max_length=2000, verbose_name='\u4efb\u52a1\u7ed3\u679c', blank=True)),
                ('fetch_time', models.DateField(null=True, verbose_name='\u83b7\u53d6\u65f6\u95f4', blank=True)),
                ('file_path_to', models.TextField(max_length=256, verbose_name='\u7ed3\u679c\u5b58\u653e\u8def\u5f84', blank=True)),
                ('create', models.DateField(auto_now=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('modified', models.DateField(auto_now_add=True, verbose_name='\u4fee\u6539\u65f6\u95f4')),
                ('status', models.CharField(default=b'CREATED', max_length=32, verbose_name='\u72b6\u6001', choices=[(b'CREATED', b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe5\x88\x9b\xe5\xbb\xba'), (b'ASYNCOK', b'\xe6\xb7\x98\xe5\xae\x9d\xe5\xbc\x82\xe6\xad\xa5\xe4\xbb\xbb\xe5\x8a\xa1\xe8\xaf\xb7\xe6\xb1\x82\xe6\x88\x90\xe5\x8a\x9f'), (b'ASYNCCOMPLETE', b'\xe6\xb7\x98\xe5\xae\x9d\xe5\xbc\x82\xe6\xad\xa5\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xae\x8c\xe6\x88\x90'), (b'DOWNLOAD', b'\xe5\xbc\x82\xe6\xad\xa5\xe4\xbb\xbb\xe5\x8a\xa1\xe7\xbb\x93\xe6\x9e\x9c\xe5\xb7\xb2\xe4\xb8\x8b\xe8\xbd\xbd\xe6\x9c\xac\xe5\x9c\xb0'), (b'SUCCESS', b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe5\xae\x8c\xe6\x88\x90'), (b'INVALID', b'\xe4\xbb\xbb\xe5\x8a\xa1\xe5\xb7\xb2\xe4\xbd\x9c\xe5\xba\x9f')])),
                ('params', models.CharField(max_length=1000, null=True, verbose_name='\u4efb\u52a1\u53c2\u6570', blank=True)),
            ],
            options={
                'db_table': 'shop_asynctask_taobao',
                'verbose_name': '\u6dd8\u5b9d\u5f02\u6b65\u4efb\u52a1',
                'verbose_name_plural': '\u6dd8\u5b9d\u5f02\u6b65\u4efb\u52a1\u5217\u8868',
            },
        ),
    ]
