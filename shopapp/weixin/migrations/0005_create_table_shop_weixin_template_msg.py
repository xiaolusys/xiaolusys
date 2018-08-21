# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0004_create_table_shop_weixin_fans'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeixinTplMsg',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wx_template_id', models.CharField(max_length=255, verbose_name='\u5fae\u4fe1\u6a21\u677fID')),
                ('content', models.TextField(null=True, verbose_name='\u6a21\u677f\u5185\u5bb9', blank=True)),
                ('footer', models.CharField(max_length=512, null=True, verbose_name='\u6a21\u677f\u6d88\u606f\u5c3e\u90e8', blank=True)),
                ('header', models.CharField(max_length=512, null=True, verbose_name='\u6a21\u677f\u6d88\u606f\u5934\u90e8', blank=True)),
                ('status', models.BooleanField(default=True, verbose_name='\u4f7f\u7528')),
            ],
            options={
                'db_table': 'shop_weixin_template_msg',
                'verbose_name': '\u5fae\u4fe1\u6a21\u677f\u6d88\u606f',
            },
        ),
    ]
