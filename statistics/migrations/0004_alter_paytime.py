# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0003_add_outer_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='saleorderstatsrecord',
            name='pay_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u4ed8\u6b3e\u65f6\u95f4', blank=True),
        ),
    ]
