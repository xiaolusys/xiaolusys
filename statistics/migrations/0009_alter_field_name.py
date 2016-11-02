# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0008_add_timly_record'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productstockstat',
            old_name='sku_inferior_num',
            new_name='inferior_num',
        ),
    ]
