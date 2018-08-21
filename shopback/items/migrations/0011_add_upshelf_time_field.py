# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0010_stats_add_adjust'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='upshelf_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u4e0a\u67b6\u65f6\u95f4', blank=True),
        )
    ]
