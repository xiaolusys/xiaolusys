# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0041_create_modelproduct_contrast'),
    ]

    operations = [
        migrations.AlterField(
            model_name='budgetlog',
            name='budget_log_type',
            field=models.CharField(db_index=True, max_length=8, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(b'envelop', '\u7ea2\u5305'), (b'refund', '\u9000\u6b3e'), (b'consum', '\u6d88\u8d39'), (b'cashout', '\u63d0\u73b0'), (b'mmcash', '\u4ee3\u7406\u63d0\u73b0\u81f3\u4f59\u989d'), (b'rfan', '\u63a8\u8350\u7c89\u4e1d'), (b'subs', '\u5173\u6ce8')]),
        ),
        migrations.AlterField(
            model_name='cushoppros',
            name='pro_status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u5546\u54c1\u72b6\u6001', choices=[(1, '\u4e0a\u67b6'), (0, '\u4e0b\u67b6')]),
        ),
        migrations.AlterField(
            model_name='integral',
            name='integral_user',
            field=models.BigIntegerField(unique=True, verbose_name='\u7528\u6237ID'),
        ),
        migrations.AlterField(
            model_name='modelproduct',
            name='lowest_agent_price',
            field=models.FloatField(default=0.0, verbose_name='\u6700\u4f4e\u552e\u4ef7', db_index=True),
        ),
        migrations.AlterField(
            model_name='saletrade',
            name='channel',
            field=models.CharField(blank=True, max_length=16, verbose_name='\u4ed8\u6b3e\u65b9\u5f0f', db_index=True, choices=[(b'budget', '\u5c0f\u9e7f\u94b1\u5305'), (b'wallet', '\u5988\u5988\u94b1\u5305'), (b'wx', '\u5fae\u4fe1APP'), (b'alipay', '\u652f\u4ed8\u5b9dAPP'), (b'wx_pub', '\u5fae\u4fe1WAP'), (b'alipay_wap', '\u652f\u4ed8\u5b9dWAP'), (b'upmp_wap', '\u94f6\u8054'), (b'applepay_upacp', 'ApplePay')]),
        ),
        migrations.AlterField(
            model_name='saletrade',
            name='order_type',
            field=models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u7c7b\u578b', choices=[(0, '\u7279\u5356\u8ba2\u5355'), (1, '\u9884\u8ba2\u5236'), (3, '\u56e2\u8d2d\u8ba2\u5355'), (2, '\u62bc\u91d1\u8ba2\u5355')]),
        ),
        migrations.AlterField(
            model_name='shoppingcart',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, '\u7279\u5356\u8ba2\u5355'), (3, '\u56e2\u8d2d\u8ba2\u5355'), (4, '\u79d2\u6740\u8ba2\u5355')]),
        ),
    ]
