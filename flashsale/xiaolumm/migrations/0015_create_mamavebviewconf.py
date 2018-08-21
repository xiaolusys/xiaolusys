# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0014_change_default_renwtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaVebViewConf',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('version', models.CharField(max_length=32, verbose_name='\u7248\u672c\u53f7', db_index=True)),
                ('is_valid', models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u6709\u6548')),
                ('extra', jsonfield.fields.JSONField(default={}, max_length=2048, null=True, verbose_name='\u914d\u7f6e\u5185\u5bb9', blank=True)),
            ],
            options={
                'db_table': 'flashsale_xlmm_webview_config',
                'verbose_name': '\u5ba2\u6237\u7aef\u5988\u5988\u9875\u9762webview\u914d\u7f6e\u8868',
                'verbose_name_plural': '\u5ba2\u6237\u7aef\u5988\u5988\u9875\u9762webview\u914d\u7f6e\u5217\u8868',
            },
        ),
    ]
