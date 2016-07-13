# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0005_tmpsharecoupon_add_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='usercoupon',
            name='is_pushed',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u63a8\u9001'),
        ),
        migrations.AlterField(
            model_name='coupontemplate',
            name='coupon_type',
            field=models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f'), (6, '\u6d3b\u52a8\u5206\u4eab'), (7, '\u63d0\u73b0\u5151\u6362')]),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='coupon_type',
            field=models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f'), (6, '\u6d3b\u52a8\u5206\u4eab'), (7, '\u63d0\u73b0\u5151\u6362')]),
        ),
    ]
