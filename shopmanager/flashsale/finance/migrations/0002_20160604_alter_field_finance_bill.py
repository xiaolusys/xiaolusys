# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='attachment',
            field=models.CharField(max_length=128, verbose_name='\u9644\u4ef6', blank=True),
        ),
    ]
