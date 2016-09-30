# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0019_auto_20160913_1640'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='failed_retrieve_time',
            field=models.DateTimeField(default=None, null=True, verbose_name='\u5feb\u9012\u67e5\u8be2\u5931\u8d25\u65f6\u95f4'),
        )
    ]
