# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('refunds', '0003_auto_20160428_1600'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refundproduct',
            name='oid',
            field=models.CharField(default=b'', unique=True, max_length=64, verbose_name=b'\xe5\xad\x90\xe8\xae\xa2\xe5\x8d\x95ID', blank=True),
        ),
    ]
