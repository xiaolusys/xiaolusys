# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0015_orderlist_bill_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='sys_status',
            field=models.CharField(default=b'draft', max_length=16, verbose_name='\u7cfb\u7edf\u72b6\u6001', db_index=True, choices=[(b'draft', '\u8349\u7a3f'), (b'approval', '\u5df2\u5ba1\u6838'), (b'billing', '\u7ed3\u7b97\u4e2d'), (b'finished', '\u5df2\u7ed3\u7b97'), (b'close', '\u5df2\u53d6\u6d88')]),
        ),
    ]
