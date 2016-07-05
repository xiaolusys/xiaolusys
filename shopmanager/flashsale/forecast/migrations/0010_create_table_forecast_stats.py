# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0013_alter_manage_schedule_type'),
        ('forecast', '0009_add_fields_total_forecast_arrival_inbound_num'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForecastStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('buyer_name', models.CharField(max_length=32, verbose_name='\u4e70\u624b\u540d\u79f0', db_index=True)),
                ('purchaser', models.CharField(max_length=32, verbose_name='\u91c7\u8d2d\u5458\u540d\u79f0', db_index=True)),
                ('purchase_num', models.IntegerField(default=0, verbose_name='\u8ba2\u8d27\u6570\u91cf')),
                ('purchase_amount', models.IntegerField(default=0, verbose_name='\u8ba2\u8d27\u91d1\u989d')),
                ('inferior_num', models.IntegerField(default=0, verbose_name='\u6b21\u54c1\u6570\u91cf')),
                ('arrival_num', models.IntegerField(default=0, verbose_name='\u7f3a\u8d27\u6570\u91cf')),
                ('purchase_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u8ba2\u8d27\u65f6\u95f4', blank=True)),
                ('delivery_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u53d1\u8d27\u65f6\u95f4', blank=True)),
                ('arrival_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u5230\u8d27\u65f6\u95f4', blank=True)),
                ('billing_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u7b97\u65f6\u95f4', blank=True)),
                ('finished_time', models.DateTimeField(null=True, verbose_name='\u5b8c\u6210\u65f6\u95f4', blank=True)),
                ('has_lack', models.BooleanField(default=False, verbose_name='\u5230\u8d27\u7f3a\u8d27')),
                ('has_defact', models.BooleanField(default=False, verbose_name='\u6b21\u54c1')),
                ('has_overhead', models.BooleanField(default=False, verbose_name='\u591a\u5230')),
                ('has_wrong', models.BooleanField(default=False, verbose_name='\u9519\u53d1')),
                ('is_unrecordlogistic', models.BooleanField(default=False, verbose_name='\u672a\u53ca\u65f6\u50ac\u8d27')),
                ('is_timeout', models.BooleanField(default=False, verbose_name='\u9884\u6d4b\u8d85\u65f6')),
                ('is_lackclose', models.BooleanField(default=False, verbose_name='\u4e0b\u5355\u7f3a\u8d27')),
            ],
            options={
                'db_table': 'forecast_stats',
                'verbose_name': '\u9884\u6d4b\u5355\u7edf\u8ba1',
                'verbose_name_plural': '\u9884\u6d4b\u5355\u7edf\u8ba1\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='is_unrecordlogistic',
            field=models.BooleanField(default=False, verbose_name='\u672a\u53ca\u65f6\u50ac\u8d27'),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='status',
            field=models.CharField(default=b'draft', max_length=8, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'draft', '\u8349\u7a3f'), (b'approved', '\u5ba1\u6838'), (b'arrived', '\u5230\u8d27'), (b'timeout', '\u8d85\u65f6\u5173\u95ed'), (b'close', '\u7f3a\u8d27\u5173\u95ed'), (b'canceled', '\u53d6\u6d88')]),
        ),
        migrations.AddField(
            model_name='forecaststats',
            name='forecast_inbound',
            field=models.OneToOneField(verbose_name='\u9884\u6d4b\u5355', to='forecast.ForecastInbound'),
        ),
        migrations.AddField(
            model_name='forecaststats',
            name='supplier',
            field=models.ForeignKey(verbose_name='\u4f9b\u5e94\u5546', to='supplier.SaleSupplier'),
        ),
    ]
