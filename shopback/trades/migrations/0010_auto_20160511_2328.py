# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0009_auto_20160509_1420'),
    ]

    operations = [
        migrations.AlterField(
            model_name='packageorder',
            name='seller_flag',
            field=models.IntegerField(default=0, null=True, verbose_name='\u6dd8\u5b9d\u65d7\u5e1c'),
        ),
    ]
