# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workorder', '0002_auto_20160802_1746'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='dealed_part',
            field=models.TextField(blank=True, verbose_name='\u5904\u7406\u90e8\u95e8', choices=[(1, '\u884c\u653f\u90e8'), (2, '\u6280\u672f\u90e8'), (3, '\u63a8\u5e7f\u90e8'), (4, '\u8d22\u52a1\u90e8'), (5, '\u5ba2\u670d\u90e8'), (6, '\u4f9b\u5e94\u94fe\u90e8'), (7, '\u4ed3\u5e93\u90e8')]),
        ),
        migrations.AddField(
            model_name='workorder',
            name='raised_part',
            field=models.TextField(blank=True, verbose_name='\u63d0\u51fa\u90e8\u95e8', choices=[(1, '\u884c\u653f\u90e8'), (2, '\u6280\u672f\u90e8'), (3, '\u63a8\u5e7f\u90e8'), (4, '\u8d22\u52a1\u90e8'), (5, '\u5ba2\u670d\u90e8'), (6, '\u4f9b\u5e94\u94fe\u90e8'), (7, '\u4ed3\u5e93\u90e8')]),
        ),
        migrations.AddField(
            model_name='workorder',
            name='content_imgs',
            field=models.TextField(verbose_name='\u56fe\u7247URL\u94fe\u63a5(\u591a\u5f20\u8bf7\u6362\u884c)', blank=True),
        ),
    ]
