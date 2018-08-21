# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('promotion', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='xlsampleapply',
            name='event_imei',
            field=models.CharField(max_length=64, verbose_name='\u8bbe\u5907\u6807\u8bc6\u53f7', blank=True),
        ),
        migrations.AlterField(
            model_name='awardwinner',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u9886\u53d6\u72b6\u6001', choices=[(0, b'\xe6\x9c\xaa\xe9\xa2\x86\xe5\x8f\x96'), (1, b'\xe5\xb7\xb2\xe9\xa2\x86\xe5\x8f\x96'), (2, b'\xe5\xb7\xb2\xe4\xbd\x9c\xe5\xba\x9f')]),
        ),
    ]
