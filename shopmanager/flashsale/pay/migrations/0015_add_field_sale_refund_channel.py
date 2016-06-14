# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0014_add_field_modelproduct_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerefund',
            name='refund_channel',
            field=models.CharField(blank=True, max_length=16, verbose_name='\u9000\u6b3e\u65b9\u5f0f', db_index=True, choices=[(b'budget', '\u5c0f\u9e7f\u94b1\u5305'), (b'wallet', '\u5988\u5988\u94b1\u5305'), (b'wx', '\u5fae\u4fe1APP'), (b'alipay', '\u652f\u4ed8\u5b9dAPP'), (b'wx_pub', '\u5fae\u652f\u4ed8'), (b'alipay_wap', '\u652f\u4ed8\u5b9d'), (b'upmp_wap', '\u94f6\u8054')]),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='refund_status',
            field=models.IntegerField(default=0, blank=True, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe7\x8a\xb6\xe6\x80\x81', choices=[(0, b'\xe6\xb2\xa1\xe6\x9c\x89\xe9\x80\x80\xe6\xac\xbe'), (3, b'\xe9\x80\x80\xe6\xac\xbe\xe5\xbe\x85\xe5\xae\xa1'), (4, b'\xe5\x90\x8c\xe6\x84\x8f\xe7\x94\xb3\xe8\xaf\xb7'), (5, b'\xe9\x80\x80\xe8\xb4\xa7\xe5\xbe\x85\xe6\x94\xb6'), (2, b'\xe6\x8b\x92\xe7\xbb\x9d\xe9\x80\x80\xe6\xac\xbe'), (6, b'\xe7\xad\x89\xe5\xbe\x85\xe8\xbf\x94\xe6\xac\xbe'), (1, b'\xe9\x80\x80\xe6\xac\xbe\xe5\x85\xb3\xe9\x97\xad'), (7, b'\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f')]),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='channel',
            field=models.CharField(blank=True, max_length=16, verbose_name='\u4ed8\u6b3e\u65b9\u5f0f', db_index=True, choices=[(b'budget', '\u5c0f\u9e7f\u94b1\u5305'), (b'wallet', '\u5988\u5988\u94b1\u5305'), (b'wx', '\u5fae\u4fe1APP'), (b'alipay', '\u652f\u4ed8\u5b9dAPP'), (b'wx_pub', '\u5fae\u652f\u4ed8'), (b'alipay_wap', '\u652f\u4ed8\u5b9d'), (b'upmp_wap', '\u94f6\u8054')]),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='status',
            field=models.IntegerField(default=3, blank=True, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(0, b'\xe6\xb2\xa1\xe6\x9c\x89\xe9\x80\x80\xe6\xac\xbe'), (3, b'\xe9\x80\x80\xe6\xac\xbe\xe5\xbe\x85\xe5\xae\xa1'), (4, b'\xe5\x90\x8c\xe6\x84\x8f\xe7\x94\xb3\xe8\xaf\xb7'), (5, b'\xe9\x80\x80\xe8\xb4\xa7\xe5\xbe\x85\xe6\x94\xb6'), (2, b'\xe6\x8b\x92\xe7\xbb\x9d\xe9\x80\x80\xe6\xac\xbe'), (6, b'\xe7\xad\x89\xe5\xbe\x85\xe8\xbf\x94\xe6\xac\xbe'), (1, b'\xe9\x80\x80\xe6\xac\xbe\xe5\x85\xb3\xe9\x97\xad'), (7, b'\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f')]),
        ),
    ]
