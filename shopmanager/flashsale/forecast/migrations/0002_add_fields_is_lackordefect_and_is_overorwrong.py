# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.forecast.models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0005_salesupplier_delta_arrive_days'),
        ('forecast', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StagingInBound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('wave_no', models.CharField(default=flashsale.forecast.models.default_inbound_ware_no, max_length=32, verbose_name='\u5165\u5e93\u6279\u6b21', db_index=True)),
                ('forecast_inbound_detail_id', models.BigIntegerField(default=0, verbose_name='\u5173\u8054\u9884\u6d4b\u5230\u8d27\u660e\u7ec6ID', db_index=True)),
                ('ware_hourse', models.IntegerField(default=0, verbose_name='\u6240\u5c5e\u4ed3\u5e93', db_index=True)),
                ('product_id', models.IntegerField(default=0, verbose_name='\u5546\u54c1ID', db_index=True)),
                ('sku_id', models.IntegerField(default=0, verbose_name='\u89c4\u683cID', db_index=True)),
                ('record_num', models.IntegerField(default=0, verbose_name='\u5f55\u5165\u6570\u91cf')),
                ('uniq_key', models.CharField(unique=True, max_length=64)),
                ('creator', models.CharField(max_length=30, verbose_name='\u64cd\u4f5c\u5458', db_index=True)),
                ('status', models.CharField(default=b'staging', max_length=16, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'staging', '\u5f85\u5165\u5e93'), (b'completed', '\u5df2\u5165\u5e93'), (b'canceled', '\u5df2\u53d6\u6d88')])),
                ('supplier', models.ForeignKey(related_name='staging_inbound_manager', verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier')),
            ],
            options={
                'db_table': 'forecast_staging_inbound_record',
                'verbose_name': '\u5230\u8d27\u9884\u5f55\u5355',
                'verbose_name_plural': '\u5230\u8d27\u9884\u5f55\u5355\u5217\u8868',
            },
        ),
        migrations.AlterModelOptions(
            name='realinbound',
            options={'verbose_name': 'V2\u5165\u4ed3\u5355', 'verbose_name_plural': 'V2\u5165\u4ed3\u5355\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='realinbounddetail',
            options={'verbose_name': 'V2\u5165\u4ed3\u5355\u660e\u7ec6', 'verbose_name_plural': 'V2\u5165\u4ed3\u5355\u660e\u7ec6\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='is_lackordefect',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u7f3a\u8d27\u6216\u6b21\u54c1'),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='is_overorwrong',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u591a\u5230\u6216\u9519\u8d27'),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='supplier',
            field=models.ForeignKey(related_name='forecast_inbound_manager', verbose_name='\u4f9b\u5e94\u5546', blank=True, to='supplier.SaleSupplier', null=True),
        ),
        migrations.AlterField(
            model_name='forecastinbounddetail',
            name='forecast_inbound',
            field=models.ForeignKey(related_name='details_manager', verbose_name='\u5173\u8054\u9884\u6d4b\u5355', to='forecast.ForecastInbound'),
        ),
        migrations.AlterField(
            model_name='realinbound',
            name='forecast_inbound',
            field=models.ForeignKey(related_name='real_inbound_manager', verbose_name='\u5173\u8054\u9884\u6d4b\u5230\u8d27\u5355', to='forecast.ForecastInbound', null=True),
        ),
        migrations.AlterField(
            model_name='realinbound',
            name='status',
            field=models.CharField(default=b'staging', max_length=30, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'staging', '\u5f85\u5165\u5e93'), (b'completed', '\u5df2\u5165\u5e93'), (b'canceled', '\u5df2\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='realinbound',
            name='wave_no',
            field=models.CharField(default=flashsale.forecast.models.default_inbound_ware_no, max_length=32, verbose_name='\u5165\u5e93\u6279\u6b21', db_index=True),
        ),
        migrations.AlterField(
            model_name='realinbounddetail',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_detail_manager', verbose_name='\u5165\u4ed3\u5355', to='forecast.RealInBound'),
        ),
        migrations.AlterField(
            model_name='realinbounddetail',
            name='status',
            field=models.CharField(default=b'normal', max_length=8, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6709\u6548'), (b'invalid', '\u4f5c\u5e9f')]),
        ),
    ]
