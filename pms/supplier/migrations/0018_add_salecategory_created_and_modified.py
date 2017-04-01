# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0017_create_model_supplier_figure'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleproductmanagedetail',
            options={'verbose_name': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6', 'verbose_name_plural': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6\u5217\u8868', 'permissions': [('revert_done', '\u53cd\u5b8c\u6210'), ('pic_rating', '\u4f5c\u56fe\u8bc4\u5206'), ('add_product', '\u52a0\u5165\u5e93\u5b58\u5546\u54c1'), ('eliminate_product', '\u6dd8\u6c70\u6392\u671f\u5546\u54c1'), ('reset_head_img', '\u91cd\u7f6e\u5934\u56fe')]},
        ),
        migrations.AddField(
            model_name='salecategory',
            name='grade',
            field=models.IntegerField(default=0, verbose_name='\u7c7b\u76ee\u7b49\u7ea7', db_index=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='name',
            field=models.CharField(max_length=64, verbose_name='\u7c7b\u76ee\u540d', blank=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='sort_order',
            field=models.IntegerField(default=0, verbose_name='\u6743\u503c'),
        ),
        migrations.AlterField(
            model_name='saleproductmanagedetail',
            name='schedule_type',
            field=models.CharField(default=b'sale', max_length=16, verbose_name='\u6392\u671f\u7c7b\u578b', db_index=True, choices=[(b'brand', '\u54c1\u724c'), (b'atop', 'TOP\u699c'), (b'topic', '\u4e13\u9898'), (b'sale', '\u7279\u5356')]),
        ),
    ]
