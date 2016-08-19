# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0026_add_status_sale_time_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='salesupplier',
            name='qq',
            field=models.CharField(max_length=32, verbose_name='QQ\u53f7\u7801', blank=True),
        ),
        migrations.AddField(
            model_name='salesupplier',
            name='weixin',
            field=models.CharField(help_text='\u4e0d\u8981\u586b\u5199\u5fae\u4fe1\u6635\u79f0', max_length=32, verbose_name='\u5fae\u4fe1\u53f7', blank=True),
        ),
        migrations.AlterField(
            model_name='salesupplier',
            name='supplier_name',
            field=models.CharField(unique=True, max_length=64, verbose_name='\u4f9b\u5e94\u5546\u540d', db_index=True),
        ),
        migrations.AlterField(
            model_name='salesupplier',
            name='ware_by',
            field=models.SmallIntegerField(default=1, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (4, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
    ]
