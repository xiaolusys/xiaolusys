# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0003_add_index_to_order_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeixinFans',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('openid', models.CharField(max_length=32, verbose_name='OPENID')),
                ('app_key', models.CharField(max_length=24, verbose_name='APPKEY')),
                ('unionid', models.CharField(max_length=32, verbose_name='UNIONID')),
                ('subscribe', models.BooleanField(default=False, verbose_name='\u8ba2\u9605\u8be5\u53f7')),
                ('subscribe_time', models.DateTimeField(null=True, verbose_name='\u8ba2\u9605\u65f6\u95f4', blank=True)),
                ('unsubscribe_time', models.DateTimeField(null=True, verbose_name='\u53d6\u6d88\u8ba2\u9605\u65f6\u95f4', blank=True)),
            ],
            options={
                'db_table': 'shop_weixin_fans',
                'verbose_name': '\u5fae\u4fe1\u516c\u4f17\u53f7\u7c89\u4e1d',
                'verbose_name_plural': '\u5fae\u4fe1\u516c\u4f17\u597d\u7c89\u4e1d\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='weixinfans',
            unique_together=set([('unionid', 'app_key')]),
        ),
        migrations.AlterIndexTogether(
            name='weixinfans',
            index_together=set([('openid', 'app_key')]),
        ),
    ]
