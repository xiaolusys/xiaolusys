# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0005_salesupplier_delta_arrive_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproduct',
            name='tags',
            field=tagging.fields.TagField(max_length=255, null=True, verbose_name='\u6807\u7b7e', blank=True),
        ),
    ]
