# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0027_orderlist_add_purchase_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderlist',
            name='checked_time',
            field=models.DateTimeField(default=None, verbose_name='\u68c0\u51fa\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='paid_time',
            field=models.DateTimeField(default=None, verbose_name='\u652f\u4ed8\u5b8c\u6210\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='pay_time',
            field=models.DateTimeField(default=None, verbose_name='\u5f00\u59cb\u652f\u4ed8\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='receive_time',
            field=models.DateTimeField(default=None, verbose_name='\u5f00\u59cb\u6536\u8d27\u65f6\u95f4'),
        ),
        migrations.AddField(
            model_name='orderlist',
            name='received_time',
            field=models.DateTimeField(default=None, verbose_name='\u5f00\u59cb\u7ed3\u7b97\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='purchase_total_num',
            field=models.IntegerField(default=0, verbose_name='\u8ba2\u8d2d\u603b\u4ef6\u6570'),
        ),
    ]
