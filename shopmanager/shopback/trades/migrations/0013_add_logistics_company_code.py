# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0012_packageskuitem_pic_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageskuitem',
            name='logistics_company_code',
            field=models.CharField(max_length=16, verbose_name='\u7269\u6d41\u516c\u53f8\u4ee3\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='out_sid',
            field=models.CharField(db_index=True, max_length=64, verbose_name='\u7269\u6d41\u7f16\u53f7', blank=True),
        ),
    ]
