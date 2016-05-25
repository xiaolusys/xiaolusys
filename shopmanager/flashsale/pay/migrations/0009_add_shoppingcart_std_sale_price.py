# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0008_add_logistic_company_code_to_useradress'),
    ]

    operations = [
        migrations.AddField(
            model_name='shoppingcart',
            name='std_sale_price',
            field=models.FloatField(default=0.0, verbose_name='\u6807\u51c6\u552e\u4ef7'),
        ),
    ]
