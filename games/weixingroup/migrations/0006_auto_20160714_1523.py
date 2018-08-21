# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0005_auto_20160714_1204'),
    ]

    operations = [
        migrations.AlterField(
            model_name='xiaoluadministrator',
            name='nick',
            field=models.CharField(default=None, max_length=64, null=True, verbose_name='\u7ba1\u7406\u5458\u6635\u79f0'),
        ),
    ]
