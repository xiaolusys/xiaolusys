# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdetail',
            name='arrival_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u5230\u8d27\u65f6\u95f4', blank=True),
        ),
    ]
