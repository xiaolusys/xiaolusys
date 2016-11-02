# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0011_useraddresschange'),
    ]

    operations = [
        migrations.RenameField(
            model_name='useraddresschange',
            old_name='sale_trade_id',
            new_name='sale_trade',
        ),
    ]
