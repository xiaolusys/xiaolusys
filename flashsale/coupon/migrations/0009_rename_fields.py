# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0008_add_coupon_transfer_record'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coupontransferrecord',
            old_name='from_nama_nick',
            new_name='from_mama_nick',
        ),
        migrations.RenameField(
            model_name='coupontransferrecord',
            old_name='to_nama_nick',
            new_name='to_mama_nick',
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='coupon_value',
            field=models.IntegerField(default=128, verbose_name='\u9762\u989d'),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='template_id',
            field=models.IntegerField(default=153, verbose_name='\u4f18\u60e0\u5238\u6a21\u7248', db_index=True),
        ),
    ]
