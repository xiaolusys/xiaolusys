# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0033_add_index_buyer_and_librarian'),
    ]

    operations = [
        migrations.AddField(
            model_name='saleproductmanage',
            name='is_sale_show',
            field=models.BooleanField(default=False, verbose_name='\u7279\u5356\u663e\u793a'),
        ),
    ]
