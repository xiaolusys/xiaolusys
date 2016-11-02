# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.forecast.models.forecast


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0012_add_forecaststats_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forecastinbound',
            name='forecast_no',
            field=models.CharField(default=flashsale.forecast.models.forecast.default_forecast_inbound_no, unique=True, max_length=32, verbose_name='\u5165\u5e93\u6279\u6b21'),
        ),
        migrations.AlterField(
            model_name='realinbounddetail',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_detail_manager', verbose_name='\u5165\u4ed3\u5355', to='forecast.RealInbound'),
        ),
    ]
