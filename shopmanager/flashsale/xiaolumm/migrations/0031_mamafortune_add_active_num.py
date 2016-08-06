# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0030_auto_20160806_1201'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamafortune',
            name='active_all_num',
            field=models.IntegerField(default=0, verbose_name='\u603b\u6fc0\u6d3b\u6570'),
        ),
        migrations.AddField(
            model_name='mamafortune',
            name='active_normal_num',
            field=models.IntegerField(default=0, verbose_name='\u666e\u901a\u5988\u5988\u6fc0\u6d3b\u6570'),
        ),
        migrations.AddField(
            model_name='mamafortune',
            name='active_trial_num',
            field=models.IntegerField(default=0, verbose_name='\u8bd5\u7528\u5988\u5988\u6fc0\u6d3b\u6570'),
        ),
    ]
