# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0028_supplier_add_return_ware_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryPreference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('preferences', jsonfield.fields.JSONField(default=[], max_length=1024, verbose_name='\u53c2\u6570\u9009\u9879')),
                ('is_default', models.BooleanField(default=False, verbose_name='\u8bbe\u4e3a\u9ed8\u8ba4')),
                ('category', models.ForeignKey(related_name='category_pool_preference', verbose_name='\u7c7b\u522b', to='supplier.SaleCategory')),
            ],
            options={
                'db_table': 'supplychain_category_preference_conf',
                'verbose_name': '\u7279\u5356/\u4ea7\u54c1\u7c7b\u522b\u53c2\u6570\u914d\u7f6e\u8868',
                'verbose_name_plural': '\u7279\u5356/\u4ea7\u54c1\u7c7b\u522b\u53c2\u6570\u914d\u7f6e\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PreferencePool',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u53c2\u6570\u540d\u79f0')),
                ('categorys', jsonfield.fields.JSONField(default=[], help_text='\u54ea\u4e9b\u7c7b\u522b(\u4fdd\u5b58id\u5217\u8868)\u5305\u542b\u672c\u53c2\u6570', max_length=512, verbose_name='\u5305\u542b\u7c7b\u522b')),
                ('preference_value', jsonfield.fields.JSONField(default=[], max_length=10240, verbose_name='\u53c2\u6570\u503c')),
            ],
            options={
                'db_table': 'supplychain_preference_pool',
                'verbose_name': '\u7279\u5356/\u4ea7\u54c1\u8d44\u6599\u53c2\u6570\u8868',
                'verbose_name_plural': '\u7279\u5356/\u4ea7\u54c1\u8d44\u6599\u53c2\u6570\u5217\u8868',
            },
        ),
    ]
