# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0022_skustock_trade'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageorder',
            name='type',
            field=models.CharField(default=b'sale', choices=[(b'fixed', '\u6dd8\u5b9d&\u5546\u57ce'), (b'fenxiao', '\u6dd8\u5b9d\u5206\u9500'), (b'sale', '\u5c0f\u9e7f\u7279\u5356'), (b'jd', '\u4eac\u4e1c\u5546\u57ce'), (b'yhd', '\u4e00\u53f7\u5e97'), (b'dd', '\u5f53\u5f53\u5546\u57ce'), (b'sn', '\u82cf\u5b81\u6613\u8d2d'), (b'wx', '\u5fae\u4fe1\u5c0f\u5e97'), (b'amz', '\u4e9a\u9a6c\u900a'), (b'direct', '\u5185\u552e'), (b'reissue', '\u8865\u53d1'), (b'exchange', '\u9000\u6362\u8d27')], max_length=32, blank=True, verbose_name='\u8ba2\u5355\u7c7b\u578b', db_index=True),
        ),
    ]
