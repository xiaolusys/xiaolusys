# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0023_salecategoryversion'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleproductmanagedetail',
            options={'verbose_name': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6', 'verbose_name_plural': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6\u5217\u8868', 'permissions': [('revert_done', '\u53cd\u5b8c\u6210'), ('pic_rating', '\u4f5c\u56fe\u8bc4\u5206'), ('add_product', '\u52a0\u5165\u5e93\u5b58\u5546\u54c1'), ('eliminate_product', '\u6dd8\u6c70\u6392\u671f\u5546\u54c1'), ('reset_head_img', '\u91cd\u7f6e\u5934\u56fe'), ('delete_schedule_detail', '\u5220\u9664\u6392\u671f\u660e\u7ec6\u8bb0\u5f55'), ('distribute_schedule_detail', '\u6392\u671f\u7ba1\u7406\u4efb\u52a1\u5206\u914d')]},
        ),
        migrations.AlterField(
            model_name='salesupplier',
            name='ware_by',
            field=models.SmallIntegerField(default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3')]),
        ),
    ]
