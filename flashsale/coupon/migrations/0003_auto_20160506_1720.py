# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0002_auto_20160503_1902'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coupontemplate',
            name='coupon_type',
            field=models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f'), (6, '\u6d3b\u52a8\u5206\u4eab')]),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='coupon_type',
            field=models.IntegerField(default=1, verbose_name='\u4f18\u60e0\u5238\u7c7b\u578b', choices=[(1, '\u666e\u901a\u7c7b\u578b'), (5, '\u4e0b\u5355\u7ea2\u5305'), (2, '\u8ba2\u5355\u5206\u4eab'), (3, '\u63a8\u8350\u4e13\u4eab'), (4, '\u552e\u540e\u8865\u507f'), (6, '\u6d3b\u52a8\u5206\u4eab')]),
        ),
        migrations.AlterField(
            model_name='usercoupon',
            name='ufrom',
            field=models.CharField(blank=True, max_length=8, verbose_name='\u9886\u53d6\u5e73\u53f0', db_index=True, choices=[('wx', '\u5fae\u4fe1\u597d\u53cb'), ('pyq', '\u670b\u53cb\u5708'), ('qq', 'QQ\u597d\u53cb'), ('qq_spa', 'QQ\u7a7a\u95f4'), ('sina', '\u65b0\u6d6a\u5fae\u535a'), ('wap', 'wap'), ('tmp', '\u4e34\u65f6\u8868')]),
        ),
        migrations.AlterUniqueTogether(
            name='tmpsharecoupon',
            unique_together=set([('mobile', 'share_coupon_id')]),
        ),
    ]
