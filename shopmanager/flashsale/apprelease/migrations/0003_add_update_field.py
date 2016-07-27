# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apprelease', '0002_add_hash_version_code_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='apprelease',
            name='auto_update',
            field=models.BooleanField(default=True, verbose_name='\u81ea\u52a8\u66f4\u65b0'),
        ),
    ]
