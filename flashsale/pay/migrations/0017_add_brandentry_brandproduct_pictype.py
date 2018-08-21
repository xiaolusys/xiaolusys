# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0016_add_extrapic_and_brand_locationid'),
    ]

    operations = [
        migrations.AddField(
            model_name='brandentry',
            name='mask_link',
            field=models.CharField(max_length=256, verbose_name='\u4e13\u9898\u6d3b\u52a8\u5f39\u7a97\u63d0\u793a\u56fe', blank=True),
        ),
        migrations.AddField(
            model_name='brandentry',
            name='promotion_type',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u4e13\u9898\u6d3b\u52a8\u7c7b\u578b', choices=[(1, 'Top10'), (2, '\u4e13\u9898'), (3, '\u54c1\u724c')]),
        ),
        migrations.AddField(
            model_name='brandentry',
            name='share_icon',
            field=models.CharField(max_length=128, verbose_name='\u4e13\u9898\u6d3b\u52a8\u5206\u4eab\u56fe\u7247', blank=True),
        ),
        migrations.AddField(
            model_name='brandentry',
            name='share_link',
            field=models.CharField(max_length=256, verbose_name='\u4e13\u9898\u6d3b\u52a8\u5206\u4eab\u94fe\u63a5', blank=True),
        ),
        migrations.AddField(
            model_name='brandproduct',
            name='pic_type',
            field=models.IntegerField(default=6, db_index=True, verbose_name='\u56fe\u7247\u7c7b\u578b', choices=[(0, 'Banner\u56fe\u7247'), (1, '\u4f18\u60e0\u5238\u9886\u524d'), (2, '\u4f18\u60e0\u5238\u9886\u540e'), (3, '\u4e3b\u9898\u5165\u53e3'), (4, '\u5206\u7c7b\u8bf4\u660e\u56fe\u7247'), (5, '\u5546\u54c1\u6a2a\u653e\u56fe\u7247'), (6, '\u5546\u54c1\u7ad6\u653e\u56fe\u7247'), (7, '\u5e95\u90e8\u5206\u4eab\u56fe\u7247')]),
        ),
        migrations.AlterField(
            model_name='brandproduct',
            name='product_id',
            field=models.BigIntegerField(default=0, verbose_name='\u5546\u54c1ID', db_index=True),
        ),
    ]
