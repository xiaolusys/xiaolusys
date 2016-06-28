# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0009_add_schedule_type_and_sale_suppliers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saleproductmanage',
            name='sale_suppliers',
            field=models.ManyToManyField(to='supplier.SaleSupplier', verbose_name='\u6392\u671f\u4f9b\u5e94\u5546', blank=True),
        ),
    ]
