# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0007_auto_20160511_2328'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xiaolumama',
            name='openid',
            field=models.CharField(unique=True, max_length=64, verbose_name='UnionID'),
        ),
    ]
