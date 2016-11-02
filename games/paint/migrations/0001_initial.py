# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PaintAccount',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('account_name', models.CharField(unique=True, max_length=64, verbose_name='\u8d26\u53f7', blank=True)),
                ('customer_id', models.IntegerField(default=0, verbose_name='\u6765\u6e90\u8ba2\u5355\u53f7')),
                ('password', models.CharField(max_length=64, verbose_name='\u5bc6\u7801', blank=True)),
                ('mobile', models.CharField(unique=True, max_length=64, verbose_name='\u624b\u673a\u53f7', blank=True)),
                ('province', models.CharField(max_length=64, verbose_name='\u7701', blank=True)),
                ('street_addr', models.CharField(max_length=128, verbose_name='\u8857\u9053\u5730\u5740', blank=True)),
                ('is_tb', models.IntegerField(default=0, verbose_name='\u6dd8\u5b9d\u5e10\u53f7')),
                ('is_jd', models.IntegerField(default=0, verbose_name='\u4eac\u4e1c\u5e10\u53f7')),
                ('is_wx', models.IntegerField(default=0, verbose_name='\u5fae\u4fe1\u5e10\u53f7')),
                ('creater_id', models.IntegerField(default=0, verbose_name='\u521b\u5efa\u8005ID')),
                ('owner_id', models.IntegerField(default=0, verbose_name='\u62e5\u6709\u8005ID')),
                ('status', models.IntegerField(default=0, verbose_name='\u5e10\u53f7\u72b6\u6001')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
            ],
            options={
                'db_table': 'games_paint_paintaccount',
                'verbose_name': 'Paint\u5e10\u53f7',
                'verbose_name_plural': 'Paint\u5e10\u53f7\u5217\u8868',
            },
        ),
    ]
