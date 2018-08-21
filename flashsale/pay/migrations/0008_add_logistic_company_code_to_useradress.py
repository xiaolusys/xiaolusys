# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import flashsale.pay.models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0007_remove_modelproduct_sale_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='useraddress',
            name='logistic_company_code',
            field=models.CharField(max_length=16, verbose_name='\u4f18\u5148\u5feb\u9012\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='goodshelf',
            name='chd_posters',
            field=jsonfield.fields.JSONField(default=flashsale.pay.models.default_chd_poster, max_length=10240, verbose_name='\u7ae5\u88c5\u6d77\u62a5', blank=True),
        ),
        migrations.AlterField(
            model_name='goodshelf',
            name='wem_posters',
            field=jsonfield.fields.JSONField(default=flashsale.pay.models.default_wen_poster, max_length=10240, verbose_name='\u5973\u88c5\u6d77\u62a5', blank=True),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='good_status',
            field=models.IntegerField(default=1, blank=True, verbose_name=b'\xe9\x80\x80\xe8\xb4\xa7\xe5\x95\x86\xe5\x93\x81\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(0, b'\xe4\xb9\xb0\xe5\xae\xb6\xe6\x9c\xaa\xe6\x94\xb6\xe5\x88\xb0\xe8\xb4\xa7'), (1, b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe6\x94\xb6\xe5\x88\xb0\xe8\xb4\xa7'), (2, b'\xe4\xb9\xb0\xe5\xae\xb6\xe5\xb7\xb2\xe9\x80\x80\xe8\xb4\xa7'), (3, b'\xe5\x8d\x96\xe5\xae\xb6\xe7\xbc\xba\xe8\xb4\xa7')]),
        ),
    ]
