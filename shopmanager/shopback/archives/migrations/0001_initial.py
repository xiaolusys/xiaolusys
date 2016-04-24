# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Deposite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('deposite_name', models.CharField(max_length=32, verbose_name=b'\xe4\xbb\x93\xe5\xba\x93\xe5\x90\x8d', blank=True)),
                ('location', models.CharField(max_length=32, verbose_name=b'\xe4\xbb\x93\xe5\xba\x93\xe4\xbd\x8d\xe7\xbd\xae', blank=True)),
                ('in_use', models.BooleanField(default=True, verbose_name=b'\xe4\xbd\xbf\xe7\x94\xa8')),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_archives_deposite',
                'verbose_name': '\u4ed3\u5e93',
                'verbose_name_plural': '\u4ed3\u5e93\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='DepositeDistrict',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('district_no', models.CharField(max_length=32, verbose_name=b'\xe8\xb4\xa7\xe4\xbd\x8d\xe5\x8f\xb7', blank=True)),
                ('parent_no', models.CharField(max_length=32, verbose_name=b'\xe7\x88\xb6\xe8\xb4\xa7\xe4\xbd\x8d\xe5\x8f\xb7', blank=True)),
                ('location', models.CharField(max_length=64, verbose_name=b'\xe8\xb4\xa7\xe4\xbd\x8d\xe5\x90\x8d', blank=True)),
                ('in_use', models.BooleanField(default=True, verbose_name=b'\xe4\xbd\xbf\xe7\x94\xa8')),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_archives_depositedistrict',
                'verbose_name': '\u4ed3\u5e93\u8d27\u4f4d',
                'verbose_name_plural': '\u4ed3\u5e93\u8d27\u4f4d\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PurchaseType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type_name', models.CharField(max_length=32, verbose_name=b'\xe9\x87\x87\xe8\xb4\xad\xe7\xb1\xbb\xe5\x9e\x8b', blank=True)),
                ('in_use', models.BooleanField(default=True, verbose_name=b'\xe4\xbd\xbf\xe7\x94\xa8')),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_archives_purchasetype',
                'verbose_name': '\u91c7\u8d2d\u7c7b\u578b',
                'verbose_name_plural': '\u91c7\u8d2d\u7c7b\u578b\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('supplier_name', models.CharField(unique=True, max_length=32, verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('contact', models.CharField(max_length=32, verbose_name=b'\xe8\x81\x94\xe7\xb3\xbb\xe6\x96\xb9\xe5\xbc\x8f', blank=True)),
                ('phone', models.CharField(max_length=32, verbose_name=b'\xe7\x94\xb5\xe8\xaf\x9d', blank=True)),
                ('mobile', models.CharField(max_length=16, verbose_name=b'\xe6\x89\x8b\xe6\x9c\xba', blank=True)),
                ('fax', models.CharField(max_length=16, verbose_name=b'\xe4\xbc\xa0\xe7\x9c\x9f', blank=True)),
                ('zip_code', models.CharField(max_length=16, verbose_name=b'\xe9\x82\xae\xe7\xbc\x96', blank=True)),
                ('email', models.CharField(max_length=64, verbose_name=b'\xe9\x82\xae\xe7\xae\xb1', blank=True)),
                ('address', models.CharField(max_length=64, verbose_name=b'\xe5\x9c\xb0\xe5\x9d\x80', blank=True)),
                ('account_bank', models.CharField(max_length=32, verbose_name=b'\xe6\xb1\x87\xe6\xac\xbe\xe9\x93\xb6\xe8\xa1\x8c', blank=True)),
                ('account_no', models.CharField(max_length=32, verbose_name=b'\xe6\xb1\x87\xe6\xac\xbe\xe5\xb8\x90\xe5\x8f\xb7', blank=True)),
                ('main_page', models.CharField(max_length=256, verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86\xe4\xb8\xbb\xe9\xa1\xb5', blank=True)),
                ('in_use', models.BooleanField(default=True, verbose_name=b'\xe4\xbd\xbf\xe7\x94\xa8')),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_archives_supplier',
                'verbose_name': '\u4f9b\u5e94\u5546',
                'verbose_name_plural': '\u4f9b\u5e94\u5546\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SupplierType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type_name', models.CharField(max_length=32, verbose_name=b'\xe7\xb1\xbb\xe5\x9e\x8b\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('extra_info', models.TextField(verbose_name=b'\xe5\xa4\x87\xe6\xb3\xa8', blank=True)),
            ],
            options={
                'db_table': 'shop_archives_suppliertype',
                'verbose_name': '\u4f9b\u5e94\u5546\u7c7b\u578b',
                'verbose_name_plural': '\u4f9b\u5e94\u5546\u7c7b\u578b\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='supplier',
            name='supply_type',
            field=models.ForeignKey(related_name='suppliers', verbose_name=b'\xe4\xbe\x9b\xe5\xba\x94\xe5\x95\x86\xe7\xb1\xbb\xe5\x9e\x8b', to='archives.SupplierType', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='depositedistrict',
            unique_together=set([('parent_no', 'district_no')]),
        ),
    ]
