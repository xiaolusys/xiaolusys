# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import shopback.items.models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0007_auto_20160531_1638'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contrastcontent',
            name='cid',
            field=models.CharField(default=shopback.items.models.default_contrast_cid, max_length=32, verbose_name='\u5bf9\u7167\u8868\u5185\u5bb9ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='contrastcontent',
            name='name',
            field=models.CharField(unique=True, max_length=32, verbose_name='\u5bf9\u7167\u8868\u5185\u5bb9'),
        ),
    ]
