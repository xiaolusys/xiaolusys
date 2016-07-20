# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0013_add_field_saleproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelstats',
            name='schedule_manage_id',
            field=models.IntegerField(default=0, verbose_name='\u6392\u671f\u7ba1\u7406id', db_index=True),
        ),
        migrations.AddField(
            model_name='modelstats',
            name='uni_key',
            field=models.CharField(db_index=True, unique=True, max_length=64, verbose_name='uni_key', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='modelstats',
            unique_together=set([]),
        ),
    ]
