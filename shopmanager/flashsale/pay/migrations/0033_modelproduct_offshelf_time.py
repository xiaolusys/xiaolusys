# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0032_add_lowest_price_to_modelproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='offshelf_time',
            field=models.DateTimeField(default=None, null=True, verbose_name='\u4e0b\u67b6\u65f6\u95f4', db_index=True, blank=True),
        ),
    ]
