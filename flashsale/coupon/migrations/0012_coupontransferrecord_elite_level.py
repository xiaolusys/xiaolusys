# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0011_add_product_img'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupontransferrecord',
            name='elite_level',
            field=models.CharField(max_length=16, null=True, verbose_name='\u7b49\u7ea7', blank=True),
        ),
    ]
