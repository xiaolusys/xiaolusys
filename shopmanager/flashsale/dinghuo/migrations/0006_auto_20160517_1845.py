# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0005_auto_20160507_1544'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inbound',
            name='orderlist_ids',
            field=jsonfield.fields.JSONField(default=b'[]', help_text='\u5197\u4f59\u7684\u8ba2\u8d27\u5355\u5173\u8054', max_length=10240, verbose_name='\u8ba2\u8d27\u5355ID', blank=True),
        ),
        migrations.AlterField(
            model_name='inbounddetail',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(1, '\u5df2\u5206\u914d'), (2, '\u672a\u5206\u914d')]),
        ),
    ]
