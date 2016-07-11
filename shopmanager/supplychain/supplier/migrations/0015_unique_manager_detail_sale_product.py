# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0014_saleproductmanagedetail_order_weight'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='saleproductmanagedetail',
            unique_together=set([('schedule_manage', 'sale_product_id')]),
        ),
    ]
