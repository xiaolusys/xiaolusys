# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0038_xiaolumama_is_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='lessontopic',
            name='click_num',
            field=models.IntegerField(default=0, verbose_name='\u70b9\u51fb\u6570', db_index=True),
        ),
        migrations.AddField(
            model_name='lessontopic',
            name='order_weight',
            field=models.IntegerField(default=1, verbose_name='\u6392\u5e8f\u503c', db_index=True),
        ),
    ]
