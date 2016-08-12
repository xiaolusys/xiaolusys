# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0025_change_cid_parent_cid_to_charfield'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleproduct',
            options={'verbose_name': '\u7279\u5356/\u9009\u54c1', 'verbose_name_plural': '\u7279\u5356/\u9009\u54c1\u5217\u8868', 'permissions': [('sale_product_mgr', '\u7279\u5356\u5546\u54c1\u7ba1\u7406'), ('schedule_manage', '\u6392\u671f\u7ba1\u7406'), ('delete_sale_product', '\u5220\u9664\u9009\u54c1')]},
        ),
        migrations.AlterIndexTogether(
            name='saleproduct',
            index_together=set([('status', 'sale_time', 'sale_category')]),
        ),
    ]
