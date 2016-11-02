# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forecast', '0007_add_index_realinbound_product_id_and_sku_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='forecastinbound',
            name='is_lackordefect',
        ),
        migrations.RemoveField(
            model_name='forecastinbound',
            name='is_overorwrong',
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='has_defact',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u6b21\u54c1'),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='has_lack',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u7f3a\u8d27'),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='has_overhead',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u591a\u5230'),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='has_wrong',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u9519\u53d1'),
        ),
        migrations.AddField(
            model_name='forecastinbound',
            name='memo',
            field=models.TextField(max_length=1000, verbose_name='\u5907\u6ce8', blank=True),
        ),
        migrations.AlterField(
            model_name='forecastinbound',
            name='status',
            field=models.CharField(default=b'draft', max_length=8, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'draft', '\u8349\u7a3f'), (b'approved', '\u5ba1\u6838'), (b'arrived', '\u5230\u8d27'), (b'timeout', '\u8d85\u65f6\u5173\u95ed'), (b'canceled', '\u53d6\u6d88')]),
        ),
    ]
