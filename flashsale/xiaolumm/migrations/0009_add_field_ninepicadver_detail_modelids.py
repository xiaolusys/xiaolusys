# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0008_alter_field_xiaolumm_openid'),
    ]

    operations = [
        migrations.AddField(
            model_name='ninepicadver',
            name='detail_modelids',
            field=models.CharField(max_length=128, null=True, verbose_name='\u8be6\u60c5\u9875\u6b3e\u5f0fid', blank=True),
        ),
    ]
