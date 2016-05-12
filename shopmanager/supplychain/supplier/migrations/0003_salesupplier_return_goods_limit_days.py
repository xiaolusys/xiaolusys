# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0002_buyergroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesupplier',
            name='return_goods_limit_days',
            field=models.IntegerField(default=20, verbose_name='\u9000\u8d27\u622a\u6b62\u65f6\u95f4'),
        ),
    ]
