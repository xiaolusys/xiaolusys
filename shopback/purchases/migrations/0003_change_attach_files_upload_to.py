# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchases', '0002_add_index'),
    ]

    operations = [
        migrations.AlterField(
            model_name='purchase',
            name='attach_files',
            field=models.FileField(upload_to=b'file/purchase/', blank=True),
        ),
        migrations.AlterField(
            model_name='purchasestorage',
            name='attach_files',
            field=models.FileField(upload_to=b'file/storage/', blank=True),
        ),
    ]
