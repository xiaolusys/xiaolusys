# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0055_add_mamamission_target_value_award_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamamission',
            name='desc',
            field=models.TextField(null=True, verbose_name='\u4efb\u52a1\u63cf\u8ff0', blank=True),
        ),
    ]
