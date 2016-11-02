# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0005_add_table_and_change_choices'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productstockstat',
            options={'verbose_name': '\u5e93\u5b58\u7edf\u8ba1\u8868', 'verbose_name_plural': '\u5e93\u5b58\u7edf\u8ba1\u8868'},
        ),
        migrations.AlterModelTable(
            name='productstockstat',
            table='statistics_product_stock_stat',
        ),
    ]
