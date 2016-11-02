# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0036_pay_teambuy2'),
    ]

    operations = [
        migrations.AddField(
            model_name='teambuy',
            name='share_xlmm_id',
            field=models.IntegerField(default=None, verbose_name='\u5206\u4eab\u7684\u5988\u5988'),
        )
    ]
