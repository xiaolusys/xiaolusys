# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0032_mamafortune_add_hasale'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamafortune',
            name='history_cashout',
            field=models.IntegerField(default=0, verbose_name='\u5386\u53f2\u5df2\u63d0\u73b0\u6536\u76ca'),
        ),
    ]
