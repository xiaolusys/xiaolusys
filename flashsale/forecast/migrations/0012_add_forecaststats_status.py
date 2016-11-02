# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0011_rename_field_arrival_num_to_lack_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='forecaststats',
            name='status',
            field=models.CharField(default=b'staging', max_length=16, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'staging', '\u5f85\u6536\u8d27'), (b'arrival', '\u5df2\u5230\u8d27'), (b'closed', '\u5df2\u5173\u95ed')]),
        ),
        migrations.AlterField(
            model_name='realinbounddetail',
            name='inbound',
            field=models.ForeignKey(related_name='inbound_detail_manager', verbose_name='\u5165\u4ed3\u5355', to='forecast.RealInbound'),
        ),
    ]
