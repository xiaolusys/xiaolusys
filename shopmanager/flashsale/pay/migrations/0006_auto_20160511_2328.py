# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0005_add_saleorder_buyer_id_and_extras'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Coupon',
        ),
        migrations.DeleteModel(
            name='CouponPool',
        ),
    ]
