# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-18 12:03
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pay', '0072_modelproduct_outside'),
    ]

    operations = [
        migrations.CreateModel(
            name='BankAccount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('account_no', models.CharField(max_length=32, verbose_name='\u94f6\u884c\u5361\u8d26\u53f7')),
                ('account_name', models.CharField(max_length=32, verbose_name='\u94f6\u884c\u5361\u6301\u6709\u4eba\u540d\u79f0')),
                ('bank_name', models.CharField(max_length=32, verbose_name='\u94f6\u884c\u5168\u79f0')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('default', models.BooleanField(default=False, verbose_name='\u9ed8\u8ba4\u4f7f\u7528')),
                ('status', models.SmallIntegerField(choices=[(0, '\u6b63\u5e38'), (1, '\u4f5c\u5e9f')], db_index=True, verbose_name='\u72b6\u6001')),
                ('extras', jsonfield.fields.JSONField(default={}, max_length=512, verbose_name='\u9644\u52a0\u4fe1\u606f')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='\u6240\u5c5e\u7528\u6237')),
            ],
            options={
                'db_table': 'flashsale_bankaccount',
                'verbose_name': '\u7528\u6237/\u94f6\u884c\u5361',
                'verbose_name_plural': '\u7528\u6237/\u94f6\u884c\u5361',
            },
        ),
    ]
