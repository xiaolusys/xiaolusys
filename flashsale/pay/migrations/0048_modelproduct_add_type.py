# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0047_add_postage_couponnum'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='product_type',
            field=models.IntegerField(default=0, verbose_name='\u5546\u54c1\u7c7b\u578b', choices=[(0, '\u5546\u54c1'), (1, '\u865a\u62df\u5546\u54c1'), (2, '\u975e\u5356\u54c1')]),
        ),
    ]
