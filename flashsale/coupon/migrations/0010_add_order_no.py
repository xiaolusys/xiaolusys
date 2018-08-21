# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0009_rename_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupontransferrecord',
            name='init_from_mama_id',
            field=models.IntegerField(default=0, verbose_name='\u7ec8\u7aef\u5988\u5988ID', db_index=True),
        ),
        migrations.AddField(
            model_name='coupontransferrecord',
            name='order_no',
            field=models.CharField(default='', max_length=64, verbose_name='\u8ba2\u8d2d\u6807\u8bc6ID', db_index=True),
            preserve_default=False,
        ),
    ]
