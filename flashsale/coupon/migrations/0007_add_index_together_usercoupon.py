# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coupon', '0006_add_ispush_usercoupon'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercoupon',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u4f7f\u7528\u72b6\u6001', choices=[(0, '\u672a\u4f7f\u7528'), (1, '\u5df2\u4f7f\u7528'), (2, '\u51bb\u7ed3\u4e2d'), (3, '\u5df2\u7ecf\u8fc7\u671f'), (4, '\u5df2\u7ecf\u53d6\u6d88')]),
        ),
        migrations.AlterIndexTogether(
            name='usercoupon',
            index_together=set([('status', 'template_id')]),
        ),
    ]
