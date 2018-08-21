# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('promotion', '0006_create_downloadmobilerecord_downloadunionidrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='appdownloadrecord',
            name='inner_ufrom',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u5185\u90e8\u6e20\u9053',
                                      choices=[(0, '\u672a\u77e5'), (1, '\u4e8c\u7ef4\u7801'), (2, '\u6d3b\u52a8'),
                                               (3, '\u7ea2\u5305')]),
        ),
        migrations.AlterField(
            model_name='appdownloadrecord',
            name='ufrom',
            field=models.CharField(default=b'wxapp', max_length=8, verbose_name='\u6765\u81ea\u5e73\u53f0',
                                   choices=[(b'wxapp', '\u5fae\u4fe1'), (b'pyq', '\u670b\u53cb\u5708'),
                                            (b'sinawb', '\u65b0\u6d6a\u5fae\u535a'), (b'wap', 'WAP'),
                                            (b'qqspa', 'QQ\u7a7a\u95f4'), (b'app', '\u5c0f\u9e7f\u7f8e\u7f8eapp'),
                                            (b'lesson', '\u5c0f\u9e7f\u5927\u5b66')]),
        ),
    ]
