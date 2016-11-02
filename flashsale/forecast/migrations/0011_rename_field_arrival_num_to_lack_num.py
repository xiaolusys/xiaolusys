# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.forecast.models.staging


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0010_create_table_forecast_stats'),
    ]

    operations = [
        migrations.RenameField(
            model_name='forecaststats',
            old_name='arrival_num',
            new_name='lack_num',
        ),
        migrations.AlterField(
            model_name='staginginbound',
            name='wave_no',
            field=models.CharField(default=flashsale.forecast.models.staging.default_inbound_ware_no, max_length=32, verbose_name='\u5165\u5e93\u6279\u6b21', db_index=True),
        ),
    ]
