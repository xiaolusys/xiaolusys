# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0010_add_order_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupontransferrecord',
            name='product_img',
            field=models.CharField(max_length=256, verbose_name='\u4ea7\u54c1\u56fe\u7247', blank=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='coupon_from_mama_id',
            field=models.IntegerField(default=0, verbose_name='From\u5988\u5988ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='coupon_to_mama_id',
            field=models.IntegerField(default=0, verbose_name='To\u5988\u5988ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='from_mama_nick',
            field=models.CharField(max_length=64, verbose_name='From\u5988\u5988\u6635\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='from_mama_thumbnail',
            field=models.CharField(max_length=256, verbose_name='From\u5988\u5988\u5934\u50cf', blank=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='to_mama_nick',
            field=models.CharField(max_length=64, verbose_name='To\u5988\u5988\u6635\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='to_mama_thumbnail',
            field=models.CharField(max_length=256, verbose_name='To\u5988\u5988\u5934\u50cf', blank=True),
        ),
        migrations.AlterField(
            model_name='coupontransferrecord',
            name='transfer_status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6d41\u901a\u72b6\u6001', choices=[(1, '\u5f85\u5ba1\u6838'), (2, '\u5f85\u53d1\u653e'), (3, '\u5df2\u5b8c\u6210'), (4, '\u5df2\u53d6\u6d88')]),
        ),
    ]
