# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0036_add_lackgoodorder_and_order_group_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='lackgoodorder',
            name='creator',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u521b\u5efa\u8005', blank=True),
        ),
    ]
