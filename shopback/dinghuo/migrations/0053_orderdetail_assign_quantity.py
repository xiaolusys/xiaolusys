# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-03-17 17:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0052_stockbatchflowrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderdetail',
            name='assign_quantity',
            field=models.IntegerField(default=0, verbose_name='\u5206\u914d\u6570\u91cf'),
        ),
    ]
