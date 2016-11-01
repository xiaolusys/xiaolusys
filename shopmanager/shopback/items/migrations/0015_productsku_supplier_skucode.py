# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0014_product_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsku',
            name='supplier_skucode',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u4f9b\u5e94\u5546SKU\u7f16\u7801', blank=True),
        ),
    ]
