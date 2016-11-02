# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0006_forecastinbound_forecast_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='realinbounddetail',
            name='product_id',
            field=models.IntegerField(verbose_name='\u5546\u54c1ID', db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name='realinbounddetail',
            unique_together=set([('sku_id', 'inbound')]),
        ),
    ]
