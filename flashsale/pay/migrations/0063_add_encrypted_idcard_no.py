# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-03-06 09:49
from __future__ import unicode_literals

from django.db import migrations, models
import encrypted_fields.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0062_saletrade_pay_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraddress',
            name='idcard_no',
            field=encrypted_fields.fields.EncryptedCharField(blank=True, max_length=128, help_text='\u81ea\u52a8\u52a0\u5bc6\u5b58\u50a8\u3001\u8bfb\u53d6\u89e3\u7801', verbose_name='\u8eab\u4efd\u8bc1\u53f7'),
        ),
        migrations.AlterField(
            model_name='useraddress',
            name='identification_no',
            field=models.CharField(blank=True, help_text='\u51c6\u5907\u5e9f\u5f03', max_length=32, verbose_name='\u8eab\u4efd\u8bc1\u53f7\u7801'),
        ),
    ]
