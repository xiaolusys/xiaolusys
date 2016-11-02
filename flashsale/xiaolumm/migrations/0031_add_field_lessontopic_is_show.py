# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0030_auto_20160806_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessontopic',
            name='is_show',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u663e\u793a'),
        ),
    ]
