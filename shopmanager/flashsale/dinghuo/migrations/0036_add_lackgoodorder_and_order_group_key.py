# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0014_saleproductmanagedetail_order_weight'),
        ('dinghuo', '0035_inbound_returngoods'),
    ]

    operations = [
        migrations.CreateModel(
            name='LackGoodOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('product_id', models.IntegerField(verbose_name='\u5546\u54c1ID', db_index=True)),
                ('sku_id', models.IntegerField(verbose_name='\u89c4\u683cID', db_index=True)),
                ('lack_num', models.IntegerField(default=0, verbose_name='\u7f3a\u8d27\u6570\u91cf')),
                ('refund_num', models.IntegerField(default=0, verbose_name='\u9000\u6b3e\u6570\u91cf')),
                ('is_refund', models.BooleanField(default=False, verbose_name='\u5df2\u9000\u6b3e')),
                ('refund_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u9000\u6b3e\u65f6\u95f4', blank=True)),
                ('order_group_key', models.CharField(max_length=64, verbose_name='\u8ba2\u8d27\u5355\u7ec4\u4e3b\u952e')),
                ('status', models.CharField(default=b'normal', max_length=8, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u4f5c\u5e9f')])),
                ('supplier', models.ForeignKey(related_name='lackgood_manager', verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier')),
            ],
            options={
                'db_table': 'flashsale_dinghuo_lackorder',
                'verbose_name': '\u8ba2\u8d27\u7f3a\u8d27\u5546\u54c1',
                'verbose_name_plural': '\u8ba2\u8d27\u7f3a\u8d27\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='orderlist',
            name='order_group_key',
            field=models.CharField(db_index=True, max_length=128, verbose_name='\u8ba2\u8d27\u5355\u5206\u7ec4\u952e', blank=True),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='out_stock',
            field=models.BooleanField(default=False, verbose_name='\u6709\u591a\u8d27'),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='refund',
            field=models.ForeignKey(related_name='inbounds', blank=True, to='refunds.Refund', help_text='\u65e0\u6548\u5b57\u6bb5\u6682\u672a\u5220\u9664', null=True, verbose_name='\u9000\u6b3e\u5355'),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='wrong',
            field=models.BooleanField(default=False, verbose_name='\u6709\u9519\u8d27'),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='purchase_order_unikey',
            field=models.CharField(max_length=32, unique=True, null=True, verbose_name='\u8ba2\u8d27\u5355\u6807\u8bc6'),
        ),
        migrations.AlterField(
            model_name='rgdetail',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, '\u9000\u8d27\u6536\u6b3e'), (1, '\u9000\u8d27\u66f4\u6362')]),
        ),
        migrations.AlterUniqueTogether(
            name='lackgoodorder',
            unique_together=set([('order_group_key', 'sku_id')]),
        ),
    ]
