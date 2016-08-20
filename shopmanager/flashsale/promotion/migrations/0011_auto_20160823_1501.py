# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0010_stock_sale_add_product_manage'),
    ]

    operations = [
        migrations.AddField(
            model_name='stocksale',
            name='location',
            field=models.CharField(default=b'', max_length=256, verbose_name='\u5e93\u4f4d', blank=True),
        ),
        migrations.AddField(
            model_name='stocksale',
            name='sku_detail',
            field=jsonfield.fields.JSONField(default=b'{}', help_text='\u5197\u4f59\u7684\u8ba2\u8d27\u5355\u5173\u8054', max_length=10240, verbose_name='\u8ba2\u8d27\u5355ID', blank=True),
        ),
        migrations.AlterField(
            model_name='activitystocksale',
            name='activity',
            field=models.ForeignKey(verbose_name='\u4e13\u9898\u6d3b\u52a8', blank=True, to='pay.ActivityEntry', null=True),
        ),
        migrations.AlterField(
            model_name='activitystocksale',
            name='product_manage',
            field=models.ForeignKey(verbose_name='\u4e13\u9898\u6392\u671f', blank=True, to='supplier.SaleProductManage', null=True),
        ),
        migrations.AlterField(
            model_name='stocksale',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u5f85\u51fa\u552e'), (1, '\u786e\u8ba4\u51fa\u552e'), (2, '\u5173\u95ed\u51fa\u552e')]),
        ),
    ]
