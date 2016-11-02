# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0002_add_unique_index_unionid_app_key'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wxorder',
            name='order_status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u8ba2\u5355\u72b6\u6001', choices=[(1, '\u5f85\u4ed8\u6b3e'), (2, '\u5f85\u53d1\u8d27'), (3, '\u5f85\u786e\u8ba4\u6536\u8d27'), (5, '\u5df2\u5b8c\u6210'), (6, '\u5df2\u5173\u95ed'), (8, '\u7ef4\u6743\u4e2d')]),
        ),
    ]
