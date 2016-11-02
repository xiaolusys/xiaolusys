# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0009_add_shoppingcart_std_sale_price'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='shoppingcart',
            index_together=set([('buyer_id', 'item_id', 'sku_id')]),
        ),
    ]
