# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0002_add_field_imei_and_winner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xlsampleapply',
            name='event_imei',
            field=models.CharField(max_length=64, verbose_name='\u8bbe\u5907\u6807\u8bc6\u53f7'),
        ),
    ]
