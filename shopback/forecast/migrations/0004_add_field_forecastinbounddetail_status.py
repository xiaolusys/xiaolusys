# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0003_auto_20160602_2047'),
    ]

    operations = [
        migrations.AddField(
            model_name='forecastinbounddetail',
            name='status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u666e\u901a'), (1, '\u5220\u9664')]),
        ),
    ]
