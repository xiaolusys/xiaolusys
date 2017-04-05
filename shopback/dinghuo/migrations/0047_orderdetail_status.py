# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0046_sku_stock'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u662f\u5426\u5df2\u7ecf\u8ba1\u5165\u5e93\u5b58'),
        ),
    ]
