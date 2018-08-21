# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('purchases', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "alter table shop_purchases_relationship add index(outer_id, outer_sku_id);"),
        migrations.RunSQL(
            "alter table shop_purchases_paymentitem add index(purchase_id,purchase_item_id);"),
        migrations.RunSQL(
            "alter table shop_purchases_paymentitem add index(storage_id,storage_item_id);"),
        migrations.RunSQL(
            "ALTER TABLE shop_purchases_purchase AUTO_INCREMENT=10001;"),
        migrations.RunSQL(
            "ALTER TABLE shop_purchases_storage AUTO_INCREMENT=10001;"),
    ]
