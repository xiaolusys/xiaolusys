# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0015_add_shelf_time_in_manage'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='saleproductmanagedetail',
            unique_together=set([('schedule_manage', 'sale_product_id')]),
        ),
    ]
