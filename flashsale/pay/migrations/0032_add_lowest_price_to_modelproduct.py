# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0031_add_fields_to_model_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='lowest_agent_price',
            field=models.FloatField(default=0.0, verbose_name='\u6700\u4f4e\u552e\u4ef7'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='lowest_std_sale_price',
            field=models.FloatField(default=0.0, verbose_name='\u6700\u4f4e\u539f\u4ef7'),
        ),
        migrations.AlterField(
            model_name='modelproduct',
            name='salecategory',
            field=models.ForeignKey(related_name='modelproduct_set', default=None, verbose_name='\u5206\u7c7b', to='supplier.SaleCategory', null=True),
        ),
    ]
