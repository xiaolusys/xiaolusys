# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('cid', models.IntegerField(serialize=False, primary_key=True)),
                ('parent_cid', models.IntegerField(null=True, db_index=True)),
                ('name', models.CharField(max_length=32, blank=True)),
                ('is_parent', models.BooleanField(default=True)),
                ('status', models.CharField(default=b'normal', max_length=7, choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u5220\u9664')])),
                ('sort_order', models.IntegerField(null=True)),
            ],
            options={
                'db_table': 'shop_categorys_category',
                'verbose_name': '\u6dd8\u5b9d\u7c7b\u76ee',
                'verbose_name_plural': '\u6dd8\u5b9d\u7c7b\u76ee\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='CategorySaleStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('stat_date', models.DateField(verbose_name=b'\xe4\xb8\x8a\xe6\x9e\xb6\xe6\x97\xa5\xe6\x9c\x9f', db_index=True)),
                ('category', models.IntegerField(default=0, verbose_name=b'\xe4\xba\xa7\xe5\x93\x81\xe7\xb1\xbb\xe5\x88\xab', db_index=True)),
                ('sale_amount', models.FloatField(default=0.0, verbose_name=b'\xe9\x94\x80\xe5\x94\xae\xe9\x87\x91\xe9\xa2\x9d')),
                ('sale_num', models.IntegerField(default=0, verbose_name=b'\xe9\x94\x80\xe5\x94\xae\xe6\x95\xb0\xe9\x87\x8f')),
                ('pit_num', models.IntegerField(default=0, verbose_name=b'\xe5\x9d\x91\xe4\xbd\x8d\xe6\x95\xb0\xe9\x87\x8f')),
                ('collect_num', models.IntegerField(default=0, verbose_name=b'\xe5\xba\x93\xe5\xad\x98\xe6\x95\xb0\xe9\x87\x8f')),
                ('collect_amount', models.FloatField(default=0.0, verbose_name=b'\xe5\xba\x93\xe5\xad\x98\xe9\x87\x91\xe9\xa2\x9d')),
                ('stock_num', models.IntegerField(default=0, verbose_name=b'\xe8\xbf\x9b\xe8\xb4\xa7\xe6\x95\xb0\xe9\x87\x8f')),
                ('stock_amount', models.FloatField(default=0.0, verbose_name=b'\xe8\xbf\x9b\xe8\xb4\xa7\xe9\x87\x91\xe9\xa2\x9d')),
                ('refund_num', models.IntegerField(default=0, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe6\x95\xb0\xe9\x87\x8f')),
                ('refund_amount', models.FloatField(default=0.0, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe9\x87\x91\xe9\xa2\x9d')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name=b'\xe5\x88\x9b\xe5\xbb\xba\xe6\x97\xb6\xe9\x97\xb4', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name=b'\xe4\xbf\xae\xe6\x94\xb9\xe6\x97\xb6\xe9\x97\xb4')),
            ],
            options={
                'db_table': 'shop_category_stat',
                'verbose_name': '\u4ea7\u54c1\u5206\u7c7b\u7edf\u8ba1',
                'verbose_name_plural': '\u4ea7\u54c1\u5206\u7c7b\u7edf\u8ba1\u5217\u8868',
                'permissions': [('shop_category_stat', '\u4ea7\u54c1\u5206\u7c7b\u7edf\u8ba1')],
            },
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('cid', models.AutoField(serialize=False, verbose_name='\u7c7b\u76eeID', primary_key=True)),
                ('parent_cid', models.IntegerField(verbose_name='\u7236\u7c7b\u76eeID')),
                ('name', models.CharField(max_length=32, verbose_name='\u7c7b\u76ee\u540d', blank=True)),
                ('is_parent', models.BooleanField(default=True, verbose_name='\u6709\u5b50\u7c7b\u76ee')),
                ('status', models.CharField(default=b'normal', max_length=7, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u5220\u9664')])),
                ('sort_order', models.IntegerField(default=0, verbose_name='\u4f18\u5148\u7ea7', db_index=True)),
            ],
            options={
                'db_table': 'shop_categorys_productcategory',
                'verbose_name': '\u4ea7\u54c1\u7c7b\u76ee',
                'verbose_name_plural': '\u4ea7\u54c1\u7c7b\u76ee\u5217\u8868',
            },
        ),
    ]
