# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('categorys', '0002_add_category_created_and_modified'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcategory',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productcategory',
            name='grade',
            field=models.IntegerField(default=0, verbose_name='\u7b49\u7ea7', db_index=True),
        ),
        migrations.AddField(
            model_name='productcategory',
            name='modified',
            field=models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='productcategory',
            name='sort_order',
            field=models.IntegerField(default=0, verbose_name='\u6743\u503c', db_index=True),
        ),
    ]
