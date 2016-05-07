# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0004_create_brand_and_brand_product_add_amount_flow_outer_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityentry',
            name='act_type',
            field=models.CharField(db_index=True, max_length=8, verbose_name='\u6d3b\u52a8\u7c7b\u578b', choices=[(b'coupon', '\u4f18\u60e0\u5238\u6d3b\u52a8'), (b'webview', '\u5546\u57ce\u6d3b\u52a8\u9875'), (b'mama', '\u5988\u5988\u6d3b\u52a8')]),
        ),
    ]
