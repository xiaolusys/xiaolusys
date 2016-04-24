# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0002_auto_20160422_1510'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageorder',
            name='sku_num',
            field=models.IntegerField(default=0, verbose_name='SKU\u79cd\u7c7b\u6570'),
        ),
    ]
