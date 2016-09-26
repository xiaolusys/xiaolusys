# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0044_budgetlog_uni_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandproduct',
            name='jump_url',
            field=models.CharField(max_length=256, verbose_name='\u8df3\u8f6c\u94fe\u63a5', blank=True),
        ),
    ]
