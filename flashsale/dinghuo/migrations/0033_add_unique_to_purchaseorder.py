# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0032_inbound_add_ware_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderlist',
            name='status',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u72b6\u6001', choices=[('\u8349\u7a3f', '\u8349\u7a3f'), ('\u5ba1\u6838', '\u5ba1\u6838'), ('\u5df2\u4ed8\u6b3e', '\u5df2\u4ed8\u6b3e'), ('\u4f5c\u5e9f', '\u4f5c\u5e9f'), ('\u6709\u95ee\u9898', '\u6709\u6b21\u54c1\u53c8\u7f3a\u8d27'), ('5', '\u6709\u6b21\u54c1'), ('6', '\u5230\u8d27\u6570\u91cf\u95ee\u9898'), ('\u9a8c\u8d27\u5b8c\u6210', '\u9a8c\u8d27\u5b8c\u6210'), ('\u5df2\u5904\u7406', '\u5df2\u5904\u7406'), ('7', '\u6837\u54c1'), ('\u5f85\u4ed8\u6b3e', '\u5f85\u4ed8\u6b3e'), ('\u5f85\u6536\u6b3e', '\u5f85\u6536\u6b3e'), ('\u5b8c\u6210', '\u5b8c\u6210')]),
        ),
        migrations.AlterField(
            model_name='purchaseorder',
            name='uni_key',
            field=models.CharField(unique=True, max_length=32, verbose_name='\u8ba2\u8d27\u5355\u552f\u4e00ID'),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='type',
            field=models.IntegerField(default=0, verbose_name='\u9000\u8d27\u7c7b\u578b', choices=[(0, '\u9000\u8d27\u56de\u6b3e'), (1, '\u9000\u8d27\u66f4\u6362')]),
        ),
        migrations.AlterField(
            model_name='rgdetail',
            name='type',
            field=models.IntegerField(default=0, choices=[(0, '\u9000\u8d27\u6536\u6b3e'), (0, '\u9000\u8d27\u66f4\u6362')]),
        ),
    ]
