# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0013_change_forecast_no_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forecastinbound',
            name='express_code',
            field=models.CharField(blank=True, max_length=32, verbose_name='\u9884\u586b\u5feb\u9012\u516c\u53f8', choices=[('YUNDA', '\u97f5\u8fbe\u901f\u9012'), ('STO', '\u7533\u901a\u5feb\u9012'), ('ZTO', '\u4e2d\u901a\u5feb\u9012'), ('EMS', '\u90ae\u653f'), ('ZJS', '\u5b85\u6025\u9001'), ('SF', '\u987a\u4e30\u901f\u8fd0'), ('YTO', '\u5706\u901a'), ('HTKY', '\u6c47\u901a\u5feb\u9012'), ('TTKDEX', '\u5929\u5929\u5feb\u9012'), ('QFKD', '\u5168\u5cf0\u5feb\u9012'), ('DBKD', '\u5fb7\u90a6\u5feb\u9012'), ('OTHER', '\u5176\u5b83\u5feb\u9012')]),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='status',
            field=models.CharField(default=b'draft', max_length=8, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'draft', '\u8349\u7a3f'), (b'approved', '\u5ba1\u6838'), (b'arrived', '\u5230\u8d27'), (b'finished', '\u5df2\u5b8c\u6210'), (b'timeout', '\u8d85\u65f6\u5173\u95ed'), (b'close', '\u7f3a\u8d27\u5173\u95ed'), (b'canceled', '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='forecastinbounddetail',
            name='product_id',
            field=models.IntegerField(verbose_name='\u5546\u54c1ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='forecaststats',
            name='status',
            field=models.CharField(default=b'staging', max_length=16, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'staging', '\u5f85\u6536\u8d27'), (b'arrival', '\u5df2\u5230\u8d27'), (b'except', '\u5f02\u5e38\u5173\u95ed'), (b'closed', '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='realinbounddetail',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_detail_manager', verbose_name='\u5165\u4ed3\u5355', to='forecast.RealInbound'),
        ),
        migrations.AlterUniqueTogether(
            name='forecastinbounddetail',
            unique_together=set([('sku_id', 'forecast_inbound')]),
        ),
    ]
