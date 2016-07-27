# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0026_add_modelproduct_is_flatten'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productdetail',
            name='product',
            field=models.OneToOneField(related_name='details', auto_created=True, primary_key=True, serialize=False, to='items.Product', verbose_name='\u5e93\u5b58\u5546\u54c1'),
        ),
    ]
