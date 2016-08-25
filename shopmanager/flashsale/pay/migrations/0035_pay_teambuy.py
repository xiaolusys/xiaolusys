# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0034_add_saleproduct_is_watermark_to_modelproduct'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamBuy',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('creator', models.CharField(max_length=30, null=True, verbose_name='\u521b\u5efa\u8005', blank=True)),
                ('limit_time', models.DateTimeField()),
                ('limit_days', models.IntegerField(default=3, verbose_name='\u9650\u5236\u5929\u6570')),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001')),
                ('sku', models.ForeignKey(to='items.ProductSku')),
            ],
            options={
                'db_table': 'flashsale_pay_teambuy',
                'verbose_name': '\u56e2\u8d2d',
                'verbose_name_plural': '\u56e2\u8d2d\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='TeamBuyDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tid', models.CharField(unique=True, max_length=40, verbose_name='\u8ba2\u5355tid')),
                ('oid', models.CharField(unique=True, max_length=40, verbose_name='\u8ba2\u5355oid')),
                ('originizer', models.BooleanField(default=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001')),
                ('customer', models.ForeignKey(to='pay.Customer')),
                ('teambuy', models.ForeignKey(to='pay.TeamBuy')),
            ],
            options={
                'db_table': 'flashsale_pay_teambuy_detail',
                'verbose_name': '\u56e2\u8d2d\u8be6\u60c5',
                'verbose_name_plural': '\u56e2\u8d2d\u8be6\u60c5\u5217\u8868',
            },
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='is_teambuy',
            field=models.BooleanField(default=False, db_index=True, verbose_name='\u56e2\u8d2d'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='teambuy_person_num',
            field=models.IntegerField(default=3, verbose_name='\u56e2\u8d2d\u4eba\u6570'),
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='teambuy_price',
            field=models.FloatField(default=0, verbose_name='\u56e2\u8d2d\u4ef7'),
        )
    ]
