# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.forecast.models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0005_add_field_realinbound_relate_order_set'),
    ]

    operations = [
        migrations.AddField(
            model_name='forecastinbound',
            name='forecast_no',
            field=models.CharField(default=flashsale.forecast.models.default_forecast_inbound_no, db_index=True, max_length=32, verbose_name='\u5165\u5e93\u6279\u6b21'),
        ),
    ]
