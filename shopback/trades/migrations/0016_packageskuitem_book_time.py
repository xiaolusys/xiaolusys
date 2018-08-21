# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0015_add_purchase_order_unikey'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='book_time',
            field=models.DateTimeField(null=True, verbose_name='\u8ba2\u8d27\u65f6\u95f4', db_index=True),
        ),
    ]
