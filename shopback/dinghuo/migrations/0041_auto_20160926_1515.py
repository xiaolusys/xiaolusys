# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0040_dinghuo_add_third_package'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='purchasedetail',
            name='extra_num',
        ),
        migrations.RemoveField(
            model_name='purchasedetail',
            name='inferior_num',
        ),
        migrations.RemoveField(
            model_name='purchaseorder',
            name='inferior_num',
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='press_num',
            field=models.IntegerField(default=0, verbose_name='\u50ac\u4fc3\u6b21\u6570', db_index=True),
        )
    ]
