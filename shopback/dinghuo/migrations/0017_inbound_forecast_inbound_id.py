# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0016_add_field_orderlist_sys_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbound',
            name='forecast_inbound_id',
            field=models.IntegerField(null=True, verbose_name='\u5173\u8054\u9884\u6d4b\u5355ID', db_index=True),
        ),
    ]
