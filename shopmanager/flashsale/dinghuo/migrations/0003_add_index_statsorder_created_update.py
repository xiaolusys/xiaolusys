# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0002_auto_20160425_1212'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplychainstatsorder',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
        ),
        migrations.AlterField(
            model_name='supplychainstatsorder',
            name='updated',
            field=models.DateTimeField(auto_now=True, verbose_name='\u66f4\u65b0\u65e5\u671f', db_index=True),
        ),
    ]
