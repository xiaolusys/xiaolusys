# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0007_add_created_to_weixinfans'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeixinQRcodeTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('params', models.TextField(verbose_name='\u6a21\u677f\u53c2\u6570')),
                ('preview_url', models.CharField(max_length=512, null=True, verbose_name='\u56fe\u7247\u9884\u89c8\u94fe\u63a5', blank=True)),
                ('status', models.BooleanField(default=True, verbose_name='\u4f7f\u7528')),
            ],
            options={
                'db_table': 'shop_weixin_qrcode_templates',
                'verbose_name': '\u5fae\u4fe1\u4e8c\u7ef4\u7801\u6a21\u677f',
                'verbose_name_plural': '\u5fae\u4fe1\u4e8c\u7ef4\u7801\u6a21\u677f\u5217\u8868',
            },
        ),
    ]
