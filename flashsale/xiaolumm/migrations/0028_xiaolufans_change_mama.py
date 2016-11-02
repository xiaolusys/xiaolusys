# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0027_change_client_config_meta'),
    ]

    operations = [
        migrations.CreateModel(
            name='FansChangeMamaRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('old_xlmm', models.BigIntegerField(verbose_name='\u539f\u5c0f\u9e7f\u5988\u5988id')),
                ('new_xlmm', models.BigIntegerField(verbose_name='\u65b0\u5c0f\u9e7f\u5988\u5988id')),
                ('fans', models.ForeignKey(verbose_name='\u7c89\u4e1d', to='xiaolumm.XlmmFans')),
            ],
            options={
                'db_table': 'flashsale_xlmm_fans_change_mama',
                'verbose_name': '\u7c89\u4e1d\u66f4\u6362\u5988\u5988\u8bb0\u5f55',
                'verbose_name_plural': '\u7c89\u4e1d\u66f4\u6362\u5988\u5988\u8bb0\u5f55',
            },
        )
    ]
