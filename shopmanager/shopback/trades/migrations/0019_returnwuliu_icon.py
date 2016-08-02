# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0018_createtable_ReturnWuliu_20160803_1012'),
    ]

    operations = [
        migrations.AddField(
            model_name='returnwuliu',
            name='icon',
            field=models.CharField(max_length=256, verbose_name='\u7269\u6d41\u516c\u53f8\u56fe\u6807', blank=True),
        ),
    ]
