# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0003_add_unique_receipt'),
    ]

    operations = [
        migrations.AddField(
            model_name='receiptgoods',
            name='status',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u62c6\u5305'),
        ),
    ]
