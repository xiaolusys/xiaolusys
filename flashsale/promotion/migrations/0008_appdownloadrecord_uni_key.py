# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0007_add_inner_uform'),
    ]

    operations = [
        migrations.AddField(
            model_name='appdownloadrecord',
            name='uni_key',
            field=models.CharField(max_length=64, unique=True, null=True, verbose_name='\u552f\u4e00\u6807\u8bc6'),
        ),
    ]
