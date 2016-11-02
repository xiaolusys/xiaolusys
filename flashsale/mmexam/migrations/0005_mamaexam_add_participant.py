# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mmexam', '0004_create_table_mamaexam'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamaexam',
            name='participant',
            field=models.IntegerField(default=1, verbose_name='\u76ee\u6807\u7528\u6237', choices=[(1, '\u5c0f\u9e7f\u5988\u5988\u8003\u8bd5')]),
        ),
    ]
