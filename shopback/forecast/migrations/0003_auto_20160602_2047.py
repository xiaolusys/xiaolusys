# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0002_add_fields_is_lackordefect_and_is_overorwrong'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forecastinbound',
            name='ware_hourse',
        ),
        migrations.RemoveField(
            model_name='realinbound',
            name='ware_hourse',
        ),
        migrations.RemoveField(
            model_name='realinbounddetail',
            name='forecast_inbound_detail',
        ),
        migrations.RemoveField(
            model_name='staginginbound',
            name='forecast_inbound_detail_id',
        ),
        migrations.RemoveField(
            model_name='staginginbound',
            name='ware_hourse',
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='ware_house',
            field=models.IntegerField(default=0, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3')]),
        ),
        migrations.AddField(
            model_name='realinbound',
            name='ware_house',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3')]),
        ),
        migrations.AddField(
            model_name='staginginbound',
            name='forecast_inbound',
            field=models.ForeignKey(related_name='staging_records', verbose_name='\u5173\u8054\u9884\u6d4b\u5355', to='forecast.ForecastInbound', null=True),
        ),
        migrations.AddField(
            model_name='staginginbound',
            name='ware_house',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='staginginbound',
            name='supplier',
            field=models.ForeignKey(related_name='staging_inbound_manager', verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier', null=True),
        ),
    ]
