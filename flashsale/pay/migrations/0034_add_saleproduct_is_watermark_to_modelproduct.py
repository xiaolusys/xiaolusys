# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0024_auto_20160805_2100'),
        ('pay', '0033_modelproduct_offshelf_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='is_watermark',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u56fe\u7247\u6c34\u5370'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='saleproduct',
            field=models.ForeignKey(related_name='modelproduct_set', default=None, verbose_name='\u7279\u5356\u9009\u54c1', to='supplier.SaleProduct', null=True),
        ),
    ]
