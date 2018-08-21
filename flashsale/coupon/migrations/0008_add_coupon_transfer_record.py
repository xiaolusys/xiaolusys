# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0007_add_index_together_usercoupon'),
    ]

    operations = [
        migrations.CreateModel(
            name='CouponTransferRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('coupon_from_mama_id', models.IntegerField(default=0, verbose_name='\u6e90\u5934\u5988\u5988ID', db_index=True)),
                ('from_mama_thumbnail', models.CharField(max_length=256, verbose_name='\u6e90\u5934\u5988\u5988\u5934\u50cf', blank=True)),
                ('from_nama_nick', models.CharField(max_length=64, verbose_name='\u6e90\u5934\u5988\u5988\u6635\u79f0', blank=True)),
                ('coupon_to_mama_id', models.IntegerField(default=0, verbose_name='\u7ec8\u70b9\u5988\u5988ID', db_index=True)),
                ('to_mama_thumbnail', models.CharField(max_length=256, verbose_name='\u7ec8\u70b9\u5988\u5988\u5934\u50cf', blank=True)),
                ('to_nama_nick', models.CharField(max_length=64, verbose_name='\u7ec8\u70b9\u5988\u5988\u6635\u79f0', blank=True)),
                ('template_id', models.IntegerField(default=0, verbose_name='\u4f18\u60e0\u5238\u6a21\u7248', db_index=True)),
                ('coupon_value', models.IntegerField(default=0, verbose_name='\u9762\u989d')),
                ('coupon_num', models.IntegerField(default=0, verbose_name='\u6570\u91cf')),
                ('transfer_type', models.IntegerField(default=0, db_index=True, verbose_name='\u6d41\u901a\u7c7b\u578b', choices=[(1, '\u9000\u5238\u6362\u94b1'), (2, '\u8f6c\u7ed9\u4e0b\u5c5e'), (3, '\u76f4\u63a5\u4e70\u8d27'), (4, '\u82b1\u94b1\u4e70\u5238'), (5, '\u4e0b\u5c5e\u9000\u5238'), (6, '\u9000\u8d27\u9000\u5238')])),
                ('transfer_status', models.IntegerField(default=1, db_index=True, verbose_name='\u6d41\u901a\u72b6\u6001', choices=[(1, '\u5f85\u5ba1\u6838'), (2, '\u5f85\u53d1\u9001'), (3, '\u5df2\u5b8c\u6210'), (4, '\u5df2\u53d6\u6d88')])),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u65e0\u6548')])),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('date_field', models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True)),
            ],
            options={
                'db_table': 'flashsale_coupon_transfer_record',
                'verbose_name': '\u7279\u5356/\u7cbe\u54c1\u5238\u6d41\u901a\u8bb0\u5f55',
                'verbose_name_plural': '\u7279\u5356/\u7cbe\u54c1\u5238\u6d41\u901a\u8bb0\u5f55\u8868',
            },
        ),
        migrations.AlterField(
            model_name='coupontemplate',
            name='coupon_type',
            field=models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f'), (6, '\u6d3b\u52a8\u5206\u4eab'), (7, '\u63d0\u73b0\u5151\u6362'), (8, '\u53ef\u6d41\u901a\u7cbe\u54c1\u5238')]),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='coupon_type',
            field=models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f'), (6, '\u6d3b\u52a8\u5206\u4eab'), (7, '\u63d0\u73b0\u5151\u6362'), (8, '\u7cbe\u54c1\u4e13\u7528\u5238')]),
        ),
    ]
