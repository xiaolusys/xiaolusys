# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_auto_20160423_1943'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trade',
            name='trade_from',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
    ]