# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0020_xlmm_add_except_total'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamacarrytotal',
            name='activite_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0,\u5305\u542bduration_total', verbose_name='\u7279\u5b9a\u6d3b\u52a8\u6392\u540d', db_index=True),
        ),
        migrations.AddField(
            model_name='mamateamcarrytotal',
            name='activite_rank_delay',
            field=models.IntegerField(default=0, help_text='\u5355\u4f4d\u4e3a\u5206\uff0c\u6bcf\u65e5\u66f4\u65b0\uff0c\u4ececache\u4e2d\u53ef\u5b9e\u65f6\u66f4\u65b0,\u5305\u542bduration_total', verbose_name='\u7279\u5b9a\u6d3b\u52a8\u6392\u540d', db_index=True),
        ),
    ]
