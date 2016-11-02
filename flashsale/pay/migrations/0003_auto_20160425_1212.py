# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.pay.models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0002_add_default_value_func'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cushoppros',
            name='carry_scheme',
            field=models.IntegerField(default=0, verbose_name='\u8fd4\u5229\u6a21\u5f0f', db_index=True),
        ),
        migrations.AlterField(
            model_name='cushoppros',
            name='remain_num',
            field=models.IntegerField(default=0, verbose_name='\u9884\u7559\u6570\u91cf'),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='refund_no',
            field=models.CharField(default=flashsale.pay.models.default_refund_no, unique=True, max_length=32, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe7\xbc\x96\xe5\x8f\xb7'),
        ),
    ]
