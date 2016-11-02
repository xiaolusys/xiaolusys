# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0003_salesupplier_return_goods_limit_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproduct',
            name='orderlist_show_memo',
            field=models.BooleanField(default=False, verbose_name='\u8ba2\u8d27\u8be6\u60c5\u663e\u793a\u5907\u6ce8'),
        ),
    ]
