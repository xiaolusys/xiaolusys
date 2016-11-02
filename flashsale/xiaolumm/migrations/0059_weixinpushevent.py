# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0058_add_cashout_modified'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeixinPushEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('customer_id', models.IntegerField(default=0, verbose_name='\u63a5\u6536\u8005\u7528\u6237id', db_index=True)),
                ('mama_id', models.IntegerField(default=0, verbose_name='\u63a5\u6536\u8005\u5988\u5988id', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('tid', models.IntegerField(default=0, verbose_name='\u6d88\u606f\u6a21\u7248ID', choices=[(7, b'\xe6\xa8\xa1\xe7\x89\x88/\xe7\xb2\x89\xe4\xb8\x9d\xe5\xa2\x9e\xe5\x8a\xa0')])),
                ('event_type', models.IntegerField(default=0, db_index=True, verbose_name='\u4e8b\u4ef6\u7c7b\u578b', choices=[(0, '\u9080\u8bf7\u4e0a\u9650\u901a\u77e5'), (2, '\u9080\u8bf7\u5956\u52b1\u751f\u6210'), (3, '\u9080\u8bf7\u5956\u52b1\u786e\u5b9a')])),
                ('date_field', models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True)),
                ('params', jsonfield.fields.JSONField(default={}, max_length=512, null=True, verbose_name='\u53c2\u6570\u4fe1\u606f', blank=True)),
                ('to_url', models.CharField(max_length=128, verbose_name='\u8df3\u8f6c\u94fe\u63a5', blank=True)),
            ],
            options={
                'db_table': 'flashsale_xlmm_weixinpushevent',
                'verbose_name': 'V2/\u5fae\u4fe1\u63a8\u9001\u4e8b\u4ef6',
                'verbose_name_plural': 'V2/\u5fae\u4fe1\u63a8\u9001\u4e8b\u4ef6\u5217\u8868',
            },
        ),
    ]
