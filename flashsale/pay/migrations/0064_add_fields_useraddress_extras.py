# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-06 13:55
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0063_add_encrypted_idcard_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraddress',
            name='extras',
            field=jsonfield.fields.JSONField(default={}, max_length=256, verbose_name='\u9644\u52a0\u53c2\u6570'),
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='identification_no',
            field=models.CharField(blank=True, help_text='\u51c6\u5907\u5e9f\u5f03!!!', max_length=32, verbose_name='\u8eab\u4efd\u8bc1\u53f7\u7801'),
        ),
    ]
