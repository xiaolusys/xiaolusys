# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0043_create_table_checkin'),
    ]

    operations = [
        migrations.AddField(
            model_name='budgetlog',
            name='uni_key',
            field=models.CharField(max_length=128, unique=True, null=True, verbose_name='\u552f\u4e00ID'),
        ),
    ]
