# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0037_teambuy_add_share_xlmm'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppingcart',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, '\u7279\u5356\u8ba2\u5355'), (1, '\u56e2\u8d2d\u8ba2\u5355'), (2, '\u79d2\u6740\u8ba2\u5355')]),
        )
    ]
