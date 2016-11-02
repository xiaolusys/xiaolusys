# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FifthCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u54c1\u7c7b\u540d\u79f0')),
                ('code', models.IntegerField(default=1, verbose_name='\u7f16\u7801')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
            ],
            options={
                'db_table': 'supplychain_product_5th',
                'verbose_name': '5\u7ea7 \u6b3e\u5f0f\u63cf\u8ff0',
                'verbose_name_plural': '5\u7ea7 \u6b3e\u5f0f\u63cf\u8ff0',
            },
        ),
        migrations.CreateModel(
            name='FirstCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u54c1\u7c7b\u540d\u79f0')),
                ('code', models.IntegerField(default=1, verbose_name='\u7f16\u7801')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
            ],
            options={
                'db_table': 'supplychain_product_1st',
                'verbose_name': '1\u7ea7\u54c1\u7c7b',
                'verbose_name_plural': '1\u7ea7\u54c1\u7c7b\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='FourthCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u54c1\u7c7b\u540d\u79f0')),
                ('code', models.IntegerField(default=1, verbose_name='\u7f16\u7801')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
            ],
            options={
                'db_table': 'supplychain_product_4th',
                'verbose_name': '4\u7ea7 \u54c1\u724c\u540d\u79f0',
                'verbose_name_plural': '4\u7ea7 \u54c1\u724c\u540d\u79f0',
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
                ('sort_order', models.IntegerField(default=0, verbose_name='\u4f18\u5148\u7ea7')),
            ],
            options={
                'db_table': 'product_category',
                'verbose_name': '\u7279\u5356/\u4ea7\u54c1\u7c7b\u76ee',
                'verbose_name_plural': '\u7279\u5356/\u4ea7\u54c1\u7c7b\u76ee\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SecondCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u54c1\u7c7b\u540d\u79f0')),
                ('code', models.IntegerField(default=1, verbose_name='\u7f16\u7801')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('parent', models.ForeignKey(to='category.FirstCategory')),
            ],
            options={
                'db_table': 'supplychain_product_2nd',
                'verbose_name': '2\u7ea7\u54c1\u7c7b',
                'verbose_name_plural': '2\u7ea7\u54c1\u7c7b\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='SixthCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u54c1\u7c7b\u540d\u79f0')),
                ('code', models.IntegerField(default=1, verbose_name='\u7f16\u7801')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('parent', models.ForeignKey(to='category.FifthCategory')),
            ],
            options={
                'db_table': 'supplychain_product_6th',
                'verbose_name': '6\u7ea7 \u5c3a\u5bf8',
                'verbose_name_plural': '6\u7ea7 \u5c3a\u5bf8',
            },
        ),
        migrations.CreateModel(
            name='ThirdCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u54c1\u7c7b\u540d\u79f0')),
                ('code', models.IntegerField(default=1, verbose_name='\u7f16\u7801')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f')),
                ('parent', models.ForeignKey(to='category.SecondCategory')),
            ],
            options={
                'db_table': 'supplychain_product_3rd',
                'verbose_name': '3\u7ea7 \u4ea7\u54c1\u5177\u4f53\u540d\u79f0',
                'verbose_name_plural': '3\u7ea7 \u4ea7\u54c1\u5177\u4f53\u540d\u79f0',
            },
        ),
        migrations.AddField(
            model_name='fourthcategory',
            name='parent',
            field=models.ForeignKey(to='category.ThirdCategory'),
        ),
        migrations.AddField(
            model_name='fifthcategory',
            name='parent',
            field=models.ForeignKey(to='category.FourthCategory'),
        ),
    ]
