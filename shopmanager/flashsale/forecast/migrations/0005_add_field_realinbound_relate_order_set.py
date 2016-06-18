# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0017_inbound_forecast_inbound_id'),
        ('forecast', '0004_add_field_forecastinbounddetail_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='realinbound',
            name='relate_order_set',
            field=models.ManyToManyField(related_name='real_inbounds', verbose_name='\u5173\u8054\u8ba2\u8d27\u5355', to='dinghuo.OrderList'),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='express_code',
            field=models.CharField(max_length=32, verbose_name='\u9884\u586b\u5feb\u9012\u516c\u53f8', blank=True),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='express_no',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u9884\u586b\u8fd0\u5355\u53f7', blank=True),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='purchaser',
            field=models.CharField(db_index=True, max_length=30, verbose_name='\u91c7\u8d2d\u5458', blank=True),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='relate_order_set',
            field=models.ManyToManyField(related_name='forecase_inbounds', verbose_name='\u5173\u8054\u8ba2\u8d27\u5355', to='dinghuo.OrderList'),
        ),
        migrations.AlterField(
            model_name='forecastinbounddetail',
            name='product_img',
            field=models.CharField(max_length=256, verbose_name='\u5546\u54c1\u56fe\u7247', blank=True),
        ),
        migrations.AlterField(
            model_name='forecastinbounddetail',
            name='product_name',
            field=models.CharField(max_length=128, verbose_name='\u5546\u54c1\u5168\u79f0', blank=True),
        ),
    ]
