# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0014_addfield_and_unikey'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dailystat',
            options={'verbose_name': '\u5c0f\u9e7f\u8d44\u4ea7\u65e5\u7edf\u8ba1\u8868', 'verbose_name_plural': '\u5c0f\u9e7f\u8d44\u4ea7\u65e5\u7edf\u8ba1\u8868'},
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_noyouni_amount',
            field=models.FloatField(default=0, verbose_name='\u975e\u4f18\u5c3c\u91d1\u989d'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_noyouni_stock',
            field=models.FloatField(default=0, verbose_name='\u975e\u4f18\u5c3c\u5e93\u5b58'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_youni_amount',
            field=models.FloatField(default=0, verbose_name='\u603b\u4f18\u5c3c\u91d1\u989d'),
        ),
        migrations.AddField(
            model_name='dailystat',
            name='total_youni_stock',
            field=models.FloatField(default=0, verbose_name='\u603b\u4f18\u5c3c\u5e93\u5b58'),
        ),
    ]
