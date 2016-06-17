# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_remove_bill_bill_method'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bill',
            name='delete_reason',
            field=models.CharField(max_length=100, null=True, verbose_name='\u4f5c\u5e9f\u7406\u7531', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='note',
            field=models.CharField(max_length=100, verbose_name='\u5907\u6ce8', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='pay_account',
            field=models.TextField(null=True, verbose_name='\u4ed8\u6b3e\u8d26\u53f7', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='pay_taobao_link',
            field=models.TextField(null=True, verbose_name='\u6dd8\u5b9d\u94fe\u63a5', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='receive_account',
            field=models.CharField(max_length=50, null=True, verbose_name='\u6536\u6b3e\u8d26\u53f7', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='receive_name',
            field=models.CharField(max_length=16, null=True, verbose_name='\u6536\u6b3e\u4eba\u59d3\u540d', blank=True),
        ),
        migrations.AlterField(
            model_name='bill',
            name='transcation_no',
            field=models.CharField(max_length=100, null=True, verbose_name='\u4ea4\u6613\u5355\u53f7', blank=True),
        ),
    ]
