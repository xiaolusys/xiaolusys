# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import flashsale.pay.models.product


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0025_create_table_usersingleaddress'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelproduct',
            name='is_flatten',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u5e73\u94fa\u663e\u793a'),
        ),
        migrations.AlterField(
            model_name='modelproduct',
            name='extras',
            field=jsonfield.fields.JSONField(default=flashsale.pay.models.product.default_modelproduct_extras_tpl, max_length=5000, verbose_name='\u9644\u52a0\u4fe1\u606f'),
        ),
    ]
