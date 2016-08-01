# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0028_add_price_to_flashsale_favorites'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integrallog',
            name='order',
            field=jsonfield.fields.JSONField(default={}, max_length=10240, verbose_name='\u8ba2\u5355\u4fe1\u606f', blank=True),
        ),
    ]
