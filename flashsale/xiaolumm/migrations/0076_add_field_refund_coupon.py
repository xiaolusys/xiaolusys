# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2017-01-12 13:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0075_auto_20170112_0959'),
    ]

    operations = [
        migrations.AddField(
            model_name='elitemamastatus',
            name='refund_coupon_in',
            field=models.IntegerField(db_index=True, default=0, verbose_name='\u9000\u8d27\u56de\u5238\u9762\u989d'),
        ),
        migrations.AddField(
            model_name='elitemamastatus',
            name='refund_coupon_out',
            field=models.IntegerField(db_index=True, default=0, verbose_name='\u9000\u8d27\u51fa\u5238\u9762\u989d'),
        ),
    ]
