# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logistics', '0002_auto_20160422_1639'),
    ]

    operations = [
        migrations.AddField(
            model_name='logisticscompany',
            name='express_key',
            field=models.CharField(max_length=64, verbose_name=b'\xe5\xbf\xab\xe9\x80\x92\xe5\x85\xac\xe5\x8f\xb8\xe4\xbb\xa3\xe7\xa0\x81', blank=True),
        ),
    ]
