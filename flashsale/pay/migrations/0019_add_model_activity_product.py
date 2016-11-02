# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0018_add_saleordersynclog'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityProduct',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('product_id', models.BigIntegerField(default=0, verbose_name='\u5546\u54c1ID', db_index=True)),
                ('model_id', models.BigIntegerField(default=0, verbose_name='\u5546\u54c1\u6b3e\u5f0fID', db_index=True)),
                ('product_name', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u540d\u79f0', blank=True)),
                ('product_img', models.CharField(max_length=256, verbose_name='\u5546\u54c1\u56fe\u7247', blank=True)),
                ('start_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True)),
                ('location_id', models.IntegerField(default=0, verbose_name='\u4f4d\u7f6e')),
                ('pic_type', models.IntegerField(default=6, db_index=True, verbose_name='\u56fe\u7247\u7c7b\u578b', choices=[(0, 'Banner\u56fe\u7247'), (1, '\u4f18\u60e0\u5238\u9886\u524d'), (2, '\u4f18\u60e0\u5238\u9886\u540e'), (3, '\u4e3b\u9898\u5165\u53e3'), (4, '\u5206\u7c7b\u8bf4\u660e\u56fe\u7247'), (5, '\u5546\u54c1\u6a2a\u653e\u56fe\u7247'), (6, '\u5546\u54c1\u7ad6\u653e\u56fe\u7247'), (7, '\u5e95\u90e8\u5206\u4eab\u56fe\u7247')])),
            ],
            options={
                'db_table': 'flashsale_activity_product',
                'verbose_name': '\u7279\u5356/\u4e13\u9898\u5546\u54c1',
                'verbose_name_plural': '\u7279\u5356/\u4e13\u9898\u5546\u54c1\u5217\u8868',
            },
        ),
        migrations.AlterField(
            model_name='activityentry',
            name='act_type',
            field=models.CharField(db_index=True, max_length=8, verbose_name='\u6d3b\u52a8\u7c7b\u578b', choices=[(b'webview', '\u5546\u57ce\u6d3b\u52a8\u9875'), (b'brand', '\u5546\u57ceTop10'), (b'topic', '\u4e13\u9898\u6d3b\u52a8'), (b'brand', '\u54c1\u724c\u6d3b\u52a8'), (b'coupon', '\u4f18\u60e0\u5238\u6d3b\u52a8'), (b'mama', '\u5988\u5988\u6d3b\u52a8')]),
        ),
        migrations.AlterField(
            model_name='saleordersynclog',
            name='type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u7c7b\u578b', choices=[(0, '\u672a\u77e5'), (1, '\u53d1\u8d27PSI'), (2, '\u8ba2\u8d27PR'), (3, '\u8ba2\u8d27NUM'), (7, '\u5305\u88f9SKU\u5b8c\u6210\u8ba1\u6570'), (5, '\u5165\u5e93\u6709\u591a\u8d27'), (6, '\u5165\u5e93\u6709\u6b21\u54c1'), (4, '\u5305\u88f9SKU\u5b9e\u65f6\u8ba1\u6570'), (8, '\u5907\u8d27\u8ba1\u6570'), (9, '\u6709\u5e93\u5b58\u672a\u5907\u8d27')]),
        ),
        migrations.AddField(
            model_name='activityproduct',
            name='activity',
            field=models.ForeignKey(related_name='brand_products', verbose_name='\u6240\u5c5e\u4e13\u9898', to='pay.ActivityEntry'),
        ),
    ]
