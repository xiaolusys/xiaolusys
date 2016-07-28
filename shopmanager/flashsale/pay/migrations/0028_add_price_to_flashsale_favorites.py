# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0027_create_table_flashsale_favorites'),
    ]

    operations = [
        migrations.AddField(
            model_name='favorites',
            name='head_img',
            field=models.TextField(verbose_name='\u9898\u5934\u7167(\u591a\u5f20\u8bf7\u6362\u884c)', blank=True),
        ),
        migrations.AddField(
            model_name='favorites',
            name='lowest_agent_price',
            field=models.FloatField(default=0, verbose_name='\u51fa\u552e\u4ef7'),
        ),
        migrations.AddField(
            model_name='favorites',
            name='lowest_std_sale_price',
            field=models.FloatField(default=0, verbose_name='\u540a\u724c\u4ef7'),
        ),
        migrations.AddField(
            model_name='favorites',
            name='name',
            field=models.CharField(default='', max_length=64, verbose_name='\u6b3e\u5f0f\u540d\u79f0', db_index=True),
            preserve_default=False,
        ),
    ]
