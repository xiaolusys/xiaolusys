# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0058_create_user_search_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerefund',
            name='creator_id',
            field=models.BigIntegerField(null=True, verbose_name='\u53d1\u8d77\u4eba', db_index=True),
        )
    ]
