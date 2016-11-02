# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0030_add_first_paytime_to_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='is_onsale',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u7279\u4ef7/\u79d2\u6740'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='is_recommend',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u63a8\u8350\u5546\u54c1'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='is_topic',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u4e13\u9898\u5546\u54c1'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='onshelf_time',
            field=models.DateTimeField(default=None, null=True, verbose_name='\u4e0a\u67b6\u65f6\u95f4', db_index=True, blank=True),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='order_weight',
            field=models.IntegerField(default=50, verbose_name='\u6743\u503c', db_index=True),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='rebeta_scheme_id',
            field=models.IntegerField(default=0, verbose_name='\u8fd4\u5229\u8ba1\u5212ID'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='shelf_status',
            field=models.CharField(default=b'off', max_length=8, verbose_name='\u4e0a\u67b6\u72b6\u6001', db_index=True, choices=[(b'on', '\u5df2\u4e0a\u67b6'), (b'off', '\u672a\u4e0a\u67b6')]),
        ),
        migrations.AlterField(
            model_name='favorites',
            name='head_img',
            field=models.TextField(verbose_name='\u9898\u5934\u7167', blank=True),
        ),
        migrations.AlterField(
            model_name='modelproduct',
            name='status',
            field=models.CharField(default=b'normal', max_length=16, verbose_name='\u72b6\u6001', db_index=True, choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u4f5c\u5e9f')]),
        ),
    ]
