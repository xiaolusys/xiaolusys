# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0013_add_logistics_company_code'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='packageskuitem',
            options={'verbose_name': '\u5305\u88f9sku\u9879', 'verbose_name_plural': '\u5305\u88f9sku\u9879\u5217\u8868'},
        ),
    ]
