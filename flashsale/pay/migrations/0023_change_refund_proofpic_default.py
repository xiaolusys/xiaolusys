# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0022_create_district_version'),
    ]

    operations = [
        migrations.AlterField(
            model_name='districtversion',
            name='hash256',
            field=models.CharField(max_length=b'128', verbose_name='sha1\u503c', blank=True),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='proof_pic',
            field=jsonfield.fields.JSONField(default=[], max_length=10240, null=True, verbose_name='\u4f50\u8bc1\u56fe\u7247', blank=True),
        ),
    ]
