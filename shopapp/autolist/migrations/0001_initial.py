# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ItemListTask',
            fields=[
                ('num_iid', models.CharField(max_length=64, serialize=False, primary_key=True)),
                ('user_id', models.CharField(max_length=32, blank=True)),
                ('nick', models.CharField(max_length=32, blank=True)),
                ('title', models.CharField(max_length=128, blank=True)),
                ('num', models.IntegerField()),
                ('list_weekday', models.IntegerField()),
                ('list_time', models.CharField(max_length=8)),
                ('task_type', models.CharField(default=b'listing', max_length=10, blank=True, choices=[(b'listing', b'\xe4\xb8\x8a\xe6\x9e\xb6'), (b'delisting', b'\xe4\xb8\x8b\xe6\x9e\xb6')])),
                ('created_at', models.DateTimeField(auto_now=True, null=True)),
                ('status', models.CharField(default=b'unexecute', max_length=10, choices=[(b'unexecute', b'\xe6\x9c\xaa\xe6\x89\xa7\xe8\xa1\x8c'), (b'execerror', b'\xe6\x89\xa7\xe8\xa1\x8c\xe5\x87\xba\xe9\x94\x99'), (b'success', b'\xe6\x88\x90\xe5\x8a\x9f'), (b'delete', b'\xe5\x88\xa0\xe9\x99\xa4'), (b'unscheduled', b'\xe6\x9c\xaa\xe8\xae\xbe\xe5\xae\x9a')])),
            ],
            options={
                'db_table': 'shop_autolist_itemlisttask',
                'verbose_name': '\u4e0a\u67b6\u4efb\u52a1',
                'verbose_name_plural': '\u4e0a\u67b6\u4efb\u52a1\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Logs',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_iid', models.CharField(max_length=64)),
                ('cat_id', models.CharField(max_length=64)),
                ('cat_name', models.CharField(max_length=64)),
                ('outer_id', models.CharField(max_length=64)),
                ('title', models.CharField(max_length=128)),
                ('pic_url', models.URLField()),
                ('list_weekday', models.IntegerField()),
                ('list_time', models.CharField(max_length=8)),
                ('num', models.IntegerField()),
                ('task_type', models.CharField(max_length=10, blank=True)),
                ('execute_time', models.DateTimeField(auto_now_add=True, null=True)),
                ('status', models.CharField(max_length=20)),
            ],
            options={
                'db_table': 'shop_autolist_logs',
                'verbose_name': '\u4e0a\u67b6\u4efb\u52a1\u65e5\u5fd7',
                'verbose_name_plural': '\u4efb\u52a1\u65e5\u5fd7',
            },
        ),
        migrations.CreateModel(
            name='TimeSlots',
            fields=[
                ('timeslot', models.IntegerField(serialize=False, primary_key=True)),
            ],
            options={
                'ordering': ['timeslot'],
                'db_table': 'shop_autolist_timeslot',
                'verbose_name': '\u4e0a\u67b6\u65f6\u95f4\u8f74',
                'verbose_name_plural': '\u4e0a\u67b6\u65f6\u95f4\u8f74',
            },
        ),
    ]
