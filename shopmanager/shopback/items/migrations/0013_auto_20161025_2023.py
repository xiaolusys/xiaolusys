# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0012_add_modelproduct_is_flatten'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productskusalestats',
            name='product_id',
        ),
        migrations.RemoveField(
            model_name='productskusalestats',
            name='sku_id',
        ),
        migrations.AddField(
            model_name='productskusalestats',
            name='product',
            field=models.ForeignKey(verbose_name='\u5546\u54c1', to='items.Product', null=True),
        ),
        migrations.AddField(
            model_name='productskusalestats',
            name='sku',
            field=models.ForeignKey(verbose_name='SKU', to='items.ProductSku', null=True),
        ),
        migrations.AlterField(
            model_name='inferiorskustats',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='product',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
    ]
