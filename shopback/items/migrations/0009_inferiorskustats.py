# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0008_alter_field_cid_and_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='InferiorSkuStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ware_by', models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3')])),
                ('history_quantity', models.IntegerField(default=0, verbose_name='\u5386\u53f2\u5e93\u5b58\u6570')),
                ('inbound_quantity', models.IntegerField(default=0, verbose_name='\u5165\u4ed3\u5e93\u5b58\u6570')),
                ('return_quantity', models.IntegerField(default=0, verbose_name='\u5ba2\u6237\u9000\u8d27\u6570')),
                ('rg_quantity', models.IntegerField(default=0, verbose_name='\u9000\u8fd8\u4f9b\u5e94\u5546\u8d27\u6570')),
                ('adjust_num', models.IntegerField(default=0, verbose_name='\u8c03\u6574\u6570')),
                ('created', models.DateTimeField(auto_now_add=True, null=True, verbose_name='\u521b\u5efa\u65f6\u95f4', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65f6\u95f4', null=True)),
                ('status', models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, b'EFFECT'), (1, b'DISCARD')])),
                ('product', models.ForeignKey(verbose_name='\u5546\u54c1', to='items.Product', null=True)),
                ('sku', models.OneToOneField(null=True, verbose_name='SKU', to='items.ProductSku')),
            ],
            options={
                'db_table': 'shop_items_inferiorskustats',
                'verbose_name': '\u6b21\u54c1\u8bb0\u5f55',
                'verbose_name_plural': '\u6b21\u54c1\u5e93\u5b58\u5217\u8868',
            },
        ),
    ]
