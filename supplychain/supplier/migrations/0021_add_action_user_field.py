# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0020_add_unique_salecategory_cid'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleproductmanagedetail',
            options={'verbose_name': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6', 'verbose_name_plural': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6\u5217\u8868', 'permissions': [('revert_done', '\u53cd\u5b8c\u6210'), ('pic_rating', '\u4f5c\u56fe\u8bc4\u5206'), ('add_product', '\u52a0\u5165\u5e93\u5b58\u5546\u54c1'), ('eliminate_product', '\u6dd8\u6c70\u6392\u671f\u5546\u54c1'), ('reset_head_img', '\u91cd\u7f6e\u5934\u56fe'), ('delete_schedule_detail', '\u5220\u9664\u6392\u671f\u660e\u7ec6\u8bb0\u5f55'), ('distribute_schedule_detail', '\u6392\u671f\u7ba1\u7406\u4efb\u52a1\u5206\u914d')]},
        ),
        migrations.AddField(
            model_name='saleproductmanagedetail',
            name='photo_user',
            field=models.BigIntegerField(default=0, verbose_name='\u5e73\u9762\u5236\u4f5c\u4eba', db_index=True),
        ),
        migrations.AddField(
            model_name='saleproductmanagedetail',
            name='reference_user',
            field=models.BigIntegerField(default=0, verbose_name='\u8d44\u6599\u5f55\u5165\u4eba', db_index=True),
        ),
    ]
