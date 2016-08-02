# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0021_add_action_user_field'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='saleproductmanagedetail',
            options={'verbose_name': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6', 'verbose_name_plural': '\u6392\u671f\u7ba1\u7406\u660e\u7ec6\u5217\u8868', 'permissions': [('revert_done', '\u53cd\u5b8c\u6210'), ('pic_rating', '\u4f5c\u56fe\u8bc4\u5206'), ('add_product', '\u52a0\u5165\u5e93\u5b58\u5546\u54c1'), ('eliminate_product', '\u6dd8\u6c70\u6392\u671f\u5546\u54c1'), ('reset_head_img', '\u91cd\u7f6e\u5934\u56fe'), ('delete_schedule_detail', '\u5220\u9664\u6392\u671f\u660e\u7ec6\u8bb0\u5f55')]},
        ),
        migrations.AddField(
            model_name='salecategory',
            name='cat_pic',
            field=models.CharField(max_length=256, verbose_name='\u5c55\u793a\u56fe\u7247', blank=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='grade',
            field=models.IntegerField(default=0, verbose_name='\u7c7b\u76ee\u7b49\u7ea7', db_index=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='status',
            field=models.CharField(default=b'normal', max_length=7, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u672a\u4f7f\u7528')]),
        ),
    ]
