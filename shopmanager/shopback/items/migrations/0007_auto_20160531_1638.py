# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0006_auto_20160511_2328'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productskustats',
            options={'verbose_name': 'SKU\u5e93\u5b58', 'verbose_name_plural': 'SKU\u5e93\u5b58\u5217\u8868'},
        ),
        migrations.RemoveField(
            model_name='productskustats',
            name='product_id',
        ),
        migrations.RemoveField(
            model_name='productskustats',
            name='sku_id',
        ),
        migrations.AddField(
            model_name='productskustats',
            name='product',
            field=models.ForeignKey(verbose_name='\u5546\u54c1', to='items.Product', null=True),
        ),
        migrations.AddField(
            model_name='productskustats',
            name='sku',
            field=models.OneToOneField(null=True, verbose_name='SKU', to='items.ProductSku'),
        ),
        migrations.AlterField(
            model_name='productskustats',
            name='sold_num',
            field=models.IntegerField(default=0, verbose_name='\u8d2d\u4e70\u6570'),
        ),
    ]
