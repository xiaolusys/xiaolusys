# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0024_orderlist_add_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderlist',
            name='lack',
            field=models.NullBooleanField(default=None, verbose_name='\u7f3a\u8d27'),
        )
    ]
