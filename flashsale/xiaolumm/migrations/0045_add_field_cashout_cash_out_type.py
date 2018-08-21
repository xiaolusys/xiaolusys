# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0044_mamaweeklyaward'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashout',
            name='cash_out_type',
            field=models.CharField(default=b'red', max_length=8, verbose_name='\u63d0\u73b0\u7c7b\u578b', choices=[(b'renew', '\u5988\u5988\u7eed\u8d39'), (b'budget', '\u63d0\u81f3\u4f59\u989d'), (b'red', '\u5fae\u4fe1\u7ea2\u5305'), (b'coupon', '\u5151\u6362\u4f18\u60e0\u5238')]),
        ),
    ]
