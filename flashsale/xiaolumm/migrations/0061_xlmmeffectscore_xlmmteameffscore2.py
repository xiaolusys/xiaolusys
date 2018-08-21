# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0060_xlmmeffectscore_xlmmteameffscore'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xlmmeffectscore',
            name='mama_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='xlmmteameffscore',
            name='mama_id',
            field=models.IntegerField(null=True, db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name='xlmmeffectscore',
            unique_together=set([('mama_id', 'stat_time')]),
        ),
        migrations.AlterUniqueTogether(
            name='xlmmteameffscore',
            unique_together=set([('mama_id', 'stat_time')]),
        ),
    ]
