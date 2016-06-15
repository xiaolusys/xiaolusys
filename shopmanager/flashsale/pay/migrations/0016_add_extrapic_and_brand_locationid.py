# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0015_add_field_sale_refund_channel'),
    ]

    operations = [

        migrations.AddField(
            model_name='brandentry',
            name='extra_pic',
            field=jsonfield.fields.JSONField(default=[], max_length=1024, verbose_name='\u63a8\u5e7f\u5c55\u793a\u5176\u5b83\u56fe\u7247', blank=True),
        ),
        migrations.AddField(
            model_name='brandproduct',
            name='location_id',
            field=models.IntegerField(default=0, verbose_name='\u4f4d\u7f6e'),
        ),
        migrations.AddField(
            model_name='brandproduct',
            name='model_id',
            field=models.BigIntegerField(default=0, verbose_name='\u5546\u54c1\u6b3e\u5f0fID', db_index=True),
        ),
    ]
