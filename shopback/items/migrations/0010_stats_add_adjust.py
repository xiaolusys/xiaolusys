# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0009_inferiorskustats'),
    ]

    operations = [
        migrations.AddField(
            model_name='productskustats',
            name='adjust_quantity',
            field=models.IntegerField(default=0, verbose_name='\u8c03\u6574\u6570'),
        )
    ]
