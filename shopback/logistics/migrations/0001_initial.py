# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.BigIntegerField(serialize=False, verbose_name=b'\xe5\x9c\xb0\xe5\x8c\xba\xe7\xbc\x96\xe5\x8f\xb7', primary_key=True)),
                ('parent_id', models.BigIntegerField(default=0, verbose_name=b'\xe7\x88\xb6\xe7\xba\xa7\xe7\xbc\x96\xe5\x8f\xb7', db_index=True)),
                ('type', models.IntegerField(default=0, verbose_name=b'\xe5\x8c\xba\xe5\x9f\x9f\xe7\xb1\xbb\xe5\x9e\x8b', choices=[(1, b'country/\xe5\x9b\xbd\xe5\xae\xb6'), (2, b'province/\xe7\x9c\x81/\xe8\x87\xaa\xe6\xb2\xbb\xe5\x8c\xba/\xe7\x9b\xb4\xe8\xbe\x96\xe5\xb8\x82'), (3, b'city/\xe5\x9c\xb0\xe5\x8c\xba'), (4, b'district/\xe5\x8e\xbf/\xe5\xb8\x82/\xe5\x8c\xba')])),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe5\x9c\xb0\xe5\x9f\x9f\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('zip', models.CharField(max_length=10, verbose_name=b'\xe9\x82\xae\xe7\xbc\x96', blank=True)),
            ],
            options={
                'db_table': 'shop_logistics_area',
                'verbose_name': '\u5730\u7406\u533a\u5212',
                'verbose_name_plural': '\u5730\u7406\u533a\u5212\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='DestCompany',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('state', models.CharField(max_length=64, verbose_name=b'\xe7\x9c\x81/\xe8\x87\xaa\xe6\xb2\xbb\xe5\x8c\xba/\xe7\x9b\xb4\xe8\xbe\x96\xe5\xb8\x82', blank=True)),
                ('city', models.CharField(max_length=64, verbose_name=b'\xe5\xb8\x82', blank=True)),
                ('district', models.CharField(max_length=64, verbose_name=b'\xe5\x8e\xbf/\xe5\xb8\x82/\xe5\x8c\xba', blank=True)),
                ('company', models.CharField(max_length=10, verbose_name=b'\xe5\xbf\xab\xe9\x80\x92\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
            ],
            options={
                'db_table': 'shop_logistics_destcompany',
                'verbose_name': '\u533a\u57df\u5feb\u9012\u5206\u914d',
                'verbose_name_plural': '\u533a\u57df\u5feb\u9012\u5206\u914d',
            },
        ),
        migrations.CreateModel(
            name='Logistics',
            fields=[
                ('tid', models.AutoField(serialize=False, primary_key=True)),
                ('order_code', models.CharField(max_length=64, blank=True)),
                ('is_quick_cod_order', models.BooleanField(default=True)),
                ('out_sid', models.CharField(max_length=64, blank=True)),
                ('seller_id', models.CharField(max_length=64, blank=True)),
                ('seller_nick', models.CharField(max_length=64, blank=True)),
                ('buyer_nick', models.CharField(max_length=64, blank=True)),
                ('item_title', models.CharField(max_length=64, blank=True)),
                ('delivery_start', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('delivery_end', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('receiver_name', models.CharField(max_length=64, blank=True)),
                ('receiver_phone', models.CharField(max_length=20, blank=True)),
                ('receiver_mobile', models.CharField(max_length=20, blank=True)),
                ('location', models.TextField(max_length=500, blank=True)),
                ('type', models.CharField(max_length=7, blank=True)),
                ('created', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('modified', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('seller_confirm', models.CharField(default=b'no', max_length=3)),
                ('company_name', models.CharField(max_length=32, blank=True)),
                ('is_success', models.BooleanField(default=False)),
                ('freight_payer', models.CharField(max_length=6, blank=True)),
                ('status', models.CharField(max_length=32, blank=True)),
                ('user', models.ForeignKey(related_name='logistics', to='users.User', null=True)),
            ],
            options={
                'db_table': 'shop_logistics_logistic',
                'verbose_name': '\u8ba2\u5355\u7269\u6d41',
                'verbose_name_plural': '\u8ba2\u5355\u7269\u6d41\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='LogisticsCompany',
            fields=[
                ('id', models.BigIntegerField(serialize=False, verbose_name=b'ID', primary_key=True)),
                ('code', models.CharField(unique=True, max_length=64, verbose_name=b'\xe5\xbf\xab\xe9\x80\x92\xe7\xbc\x96\xe7\xa0\x81', blank=True)),
                ('name', models.CharField(max_length=64, verbose_name=b'\xe5\xbf\xab\xe9\x80\x92\xe5\x90\x8d\xe7\xa7\xb0', blank=True)),
                ('reg_mail_no', models.CharField(max_length=500, verbose_name=b'\xe5\x8d\x95\xe5\x8f\xb7\xe5\x8c\xb9\xe9\x85\x8d\xe8\xa7\x84\xe5\x88\x99', blank=True)),
                ('district', models.TextField(verbose_name=b'\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x8c\xba\xe5\x9f\x9f(,\xe5\x8f\xb7\xe5\x88\x86\xe9\x9a\x94)', blank=True)),
                ('priority', models.IntegerField(default=0, null=True, verbose_name=b'\xe4\xbc\x98\xe5\x85\x88\xe7\xba\xa7')),
                ('status', models.BooleanField(default=True, verbose_name=b'\xe4\xbd\xbf\xe7\x94\xa8')),
            ],
            options={
                'db_table': 'shop_logistics_company',
                'verbose_name': '\u7269\u6d41\u516c\u53f8',
                'verbose_name_plural': '\u7269\u6d41\u516c\u53f8\u5217\u8868',
            },
        ),
    ]
