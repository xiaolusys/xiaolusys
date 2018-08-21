# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0034_saleproductmanage_is_sale_show'),
        ('xiaolumm', '0062_add_index_together_mamadailyappvisit'),
    ]

    operations = [
        migrations.AddField(
            model_name='ninepicadver',
            name='sale_category',
            field=models.ForeignKey(verbose_name='\u7c7b\u522b', to='supplier.SaleCategory', null=True),
        )
    ]
