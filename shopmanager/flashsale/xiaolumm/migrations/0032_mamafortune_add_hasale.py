# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0031_mamafortune_add_active_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamafortune',
            name='hasale_all_num',
            field=models.IntegerField(default=0, verbose_name='\u51fa\u8d27\u5988\u5988\u603b\u6570'),
        ),
        migrations.AddField(
            model_name='mamafortune',
            name='hasale_normal_num',
            field=models.IntegerField(default=0, verbose_name='\u51fa\u8d27\u666e\u901a\u5988\u5988\u6570'),
        ),
        migrations.AddField(
            model_name='mamafortune',
            name='hasale_trial_num',
            field=models.IntegerField(default=0, verbose_name='\u51fa\u8d27\u8bd5\u7528\u5988\u5988\u6570'),
        ),
    ]
