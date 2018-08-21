# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='KefuPerformance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kefu_id', models.BigIntegerField(verbose_name='\u5ba2\u670dID', db_index=True)),
                ('kefu_name', models.CharField(max_length=32, verbose_name='\u5ba2\u670d\u540d\u5b57', db_index=True)),
                ('operation', models.CharField(db_index=True, max_length=32, verbose_name='\u64cd\u4f5c', choices=[('check', '\u5ba1\u6838\u8ba2\u5355'), ('review', '\u91cd\u5ba1\u8ba2\u5355'), ('delay', '\u5ef6\u65f6')])),
                ('trade_id', models.BigIntegerField(verbose_name='\u8ba2\u5355ID')),
                ('operate_time', models.DateTimeField(verbose_name='\u64cd\u4f5c\u65f6\u95f4')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u751f\u6210\u65e5\u671f')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='\u66f4\u65b0\u65e5\u671f')),
            ],
            options={
                'db_table': 'flashsale_kefu_record',
                'verbose_name': '\u5ba2\u670d\u64cd\u4f5c\u8bb0\u5f55',
                'verbose_name_plural': '\u5ba2\u670d\u64cd\u4f5c\u8bb0\u5f55\u8868',
            },
        ),
    ]
