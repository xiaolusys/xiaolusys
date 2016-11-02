# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0004_saleproduct_orderlist_show_memo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('items', '0007_auto_20160531_1638'),
        ('dinghuo', '0009_init_purchase_order_series'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnReturnSku',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u65e0\u6548')])),
                ('reason', models.IntegerField(default=2, verbose_name='\u4e0d\u53ef\u9000\u8d27\u539f\u56e0', choices=[(1, '\u4fdd\u62a4\u5546\u54c1'), (2, '\u5546\u5bb6\u4e0d\u8bb8\u9000\u8d27'), (3, '\u5176\u5b83\u539f\u56e0')])),
                ('creater', models.ForeignKey(verbose_name='\u521b\u5efa\u4eba', to=settings.AUTH_USER_MODEL)),
                ('product', models.ForeignKey(verbose_name='\u5546\u54c1', to='items.Product', null=True)),
                ('sale_product', models.ForeignKey(verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleProduct', null=True)),
                ('sku', models.ForeignKey(verbose_name='sku', to='items.ProductSku', null=True)),
                ('supplier', models.ForeignKey(verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier', null=True)),
            ],
            options={
                'db_table': 'flashsale_dinghuo_unreturn_sku',
                'verbose_name': '\u4e0d\u53ef\u9000\u8d27\u5546\u54c1\u660e\u7ec6\u8868',
                'verbose_name_plural': '\u4e0d\u53ef\u9000\u8d27\u5546\u54c1\u660e\u7ec6\u5217\u8868',
            },
        ),
    ]
