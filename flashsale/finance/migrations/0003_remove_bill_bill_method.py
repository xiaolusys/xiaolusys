# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_20160604_alter_field_finance_bill'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bill',
            name='bill_method',
        ),
    ]
