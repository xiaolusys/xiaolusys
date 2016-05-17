# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0006_auto_20160511_2328'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='modelproduct',
            name='sale_time',
        ),
    ]
