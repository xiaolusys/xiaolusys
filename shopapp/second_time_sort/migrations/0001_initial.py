# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BatchNumberGroup',
            fields=[
                ('batch_number', models.AutoField(db_index=True, serialize=False, verbose_name='\u6279\u53f7', primary_key=True)),
                ('group', models.CharField(max_length=100, verbose_name='\u7ec4', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
            ],
            options={
                'db_table': 'batch_number_group',
                'verbose_name': '\u6279\u53f7/\u7ec4',
                'verbose_name_plural': '\u6279\u53f7/\u7ec4\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='BatchNumberOid',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('batch_number', models.IntegerField(null=True, verbose_name='\u6279\u53f7', db_index=True)),
                ('out_sid', models.CharField(null=True, max_length=64, blank=True, unique=True, verbose_name='\u7269\u6d41\u7f16\u53f7', db_index=True)),
                ('number', models.IntegerField(null=True, verbose_name='\u5e8f\u53f7', db_index=True)),
                ('group', models.CharField(max_length=100, verbose_name='\u7ec4', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u5206\u6361'), (1, '\u5206\u6361')])),
            ],
            options={
                'db_table': 'batch_number_oid',
                'verbose_name': '\u6279\u53f7/\u7269\u6d41\u5355\u53f7',
                'verbose_name_plural': '\u6279\u53f7/\u7269\u6d41\u5355\u53f7',
            },
        ),
        migrations.CreateModel(
            name='out_list_sku',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('out_sid', models.CharField(null=True, max_length=64, blank=True, unique=True, verbose_name='\u7269\u6d41\u7f16\u53f7', db_index=True)),
                ('outer_sku_id', models.CharField(max_length=20, verbose_name='\u89c4\u683c\u5916\u90e8\u7f16\u7801', blank=True)),
                ('outer_id', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u5916\u90e8\u7f16\u7801', blank=True)),
                ('amount', models.IntegerField(null=True, verbose_name='\u6570\u91cf', db_index=True)),
            ],
            options={
                'db_table': 'batch_number_oid',
                'verbose_name': '\u6279\u53f7/\u7269\u6d41\u5355\u53f7',
                'verbose_name_plural': '\u6279\u53f7/\u7269\u6d41\u5355\u53f7',
            },
        ),
    ]
