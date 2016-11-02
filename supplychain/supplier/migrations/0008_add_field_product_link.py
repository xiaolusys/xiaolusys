# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0007_add_field_is_promotion'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleproductmanagedetail',
            options={'ordering': ['-is_promotion'], 'verbose_name': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6', 'verbose_name_plural': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6\u5217\u8868', 'permissions': [('revert_done', '\u53cd\u5b8c\u6210'), ('pic_rating', '\u4f5c\u56fe\u8bc4\u5206'), ('add_product', '\u52a0\u5165\u5e93\u5b58\u5546\u54c1'), ('eliminate_product', '\u6dd8\u6c70\u6392\u671f\u5546\u54c1'), ('reset_head_img', '\u91cd\u7f6e\u5934\u56fe')]},
        ),
        migrations.AddField(
            model_name='salesupplier',
            name='product_link',
            field=models.CharField(max_length=256, verbose_name='\u5546\u54c1\u94fe\u63a5', blank=True),
        ),
    ]
