# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0011_add_upshelf_time_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='is_flatten',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u5e73\u94fa\u663e\u793a'),
        ),
        migrations.AlterField(
            model_name='productskustats',
            name='inferior_num',
            field=models.IntegerField(default=0, help_text='\u5df2\u4f5c\u5e9f\u7684\u6570\u636e', verbose_name='\u6b21\u54c1\u6570'),
        ),
    ]
