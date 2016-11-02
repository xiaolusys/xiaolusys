# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0013_orderlist_bill_method'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderlist',
            name='bill_method',
        ),
    ]
