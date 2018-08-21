# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0015_productsku_supplier_skucode'),
    ]

    operations = [
        migrations.RenameModel('ProductSkuStats', 'SkuStock')
    ]
