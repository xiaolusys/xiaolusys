# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0002_auto_20160420_1650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='outer_id',
            field=models.CharField(unique=True, max_length=32, verbose_name='\u5916\u90e8\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='productsku',
            name='outer_id',
            field=models.CharField(max_length=32, verbose_name='\u4f9b\u5e94\u5546\u8d27\u53f7/\u7f16\u7801'),
        ),
    ]
