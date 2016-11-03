# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0048_modelproduct_add_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ADManager',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('title', models.CharField(max_length=512, verbose_name='\u5e7f\u544a\u6807\u9898')),
                ('image', models.CharField(max_length=512, verbose_name='\u5e7f\u544a\u56fe\u7247', blank=True)),
                ('url', models.CharField(max_length=512, verbose_name='\u8df3\u8f6c\u94fe\u63a5')),
                ('status', models.BooleanField(default=True, verbose_name='\u4f7f\u7528')),
            ],
            options={
                'db_table': 'flashsale_admanager',
            },
        ),
    ]
