# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0057_add_date_field_uni_key_to_cashout'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashout',
            name='modified',
            field=models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='cashout',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
        ),
    ]
