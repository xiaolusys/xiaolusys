# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0008_add_field_product_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproductmanage',
            name='sale_suppliers',
            field=models.ManyToManyField(to='supplier.SaleSupplier', verbose_name='\u6392\u671f\u4f9b\u5e94\u5546'),
        ),
        migrations.AddField(
            model_name='saleproductmanage',
            name='schedule_type',
            field=models.CharField(default=b'sale', max_length=16, verbose_name='\u6392\u671f\u7c7b\u578b', db_index=True, choices=[(b'brand', '\u54c1\u724c'), (b'top', 'TOP\u699c'), (b'sale', '\u7279\u5356')]),
        ),
    ]
