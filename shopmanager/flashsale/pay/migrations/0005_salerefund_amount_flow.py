# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0004_create_brandentry_and_brandproduct'),
    ]

    operations = [
        migrations.AddField(
            model_name='salerefund',
            name='amount_flow',
            field=jsonfield.fields.JSONField(default=b'{"desc":""}', max_length=512, verbose_name='\u9000\u6b3e\u53bb\u5411', blank=True),
        ),
    ]
