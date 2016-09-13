# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0018_createtable_ReturnWuliu_20160803_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tradewuliu',
            name='content',
            field=models.TextField(max_length=5120, verbose_name='\u7269\u6d41\u8be6\u60c5', blank=True),
        ),
    ]
