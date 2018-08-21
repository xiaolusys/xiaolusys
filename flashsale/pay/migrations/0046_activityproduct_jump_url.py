# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0045_brandproduct_jump_url'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activityproduct',
            options={'verbose_name': '\u7279\u5356/\u6d3b\u52a8\u5546\u54c1', 'verbose_name_plural': '\u7279\u5356/\u6d3b\u52a8\u5546\u54c1\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='activityproduct',
            name='jump_url',
            field=models.CharField(max_length=256, verbose_name='\u8df3\u8f6c\u94fe\u63a5', blank=True),
        ),
    ]
