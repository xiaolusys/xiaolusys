# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('luckyawards', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='joiner',
            name='thumbnail',
            field=models.ImageField(upload_to=b'picture/luckyawards/', max_length=256, verbose_name='\u7167\u7247'),
        ),
    ]
