# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0004_create_brandentry_and_brandproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandentry',
            name='order_val',
            field=models.IntegerField(default=0, verbose_name='\u6392\u5e8f\u503c'),
        ),
        migrations.AddField(
            model_name='brandproduct',
            name='product_img',
            field=models.BigIntegerField(default=0, verbose_name='\u5546\u54c1\u56fe\u7247', db_index=True),
        ),
        migrations.AddField(
            model_name='brandproduct',
            name='product_name',
            field=models.BigIntegerField(default=0, verbose_name='\u5546\u54c1\u540d\u79f0', db_index=True),
        ),
        migrations.AlterField(
            model_name='brandproduct',
            name='brand',
            field=models.ForeignKey(related_name='brand_products', verbose_name='\u54c1\u724c\u7f16\u53f7id', to='pay.BrandEntry'),
        ),
    ]
