# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0003_auto_20160425_1212'),
    ]

    operations = [
        migrations.CreateModel(
            name='BrandEntry',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('brand_name', models.CharField(db_index=True, max_length=32, verbose_name='\u54c1\u724c\u540d\u79f0', blank=True)),
                ('brand_desc', models.TextField(max_length=512, verbose_name='\u54c1\u724c\u6d3b\u52a8\u63cf\u8ff0', blank=True)),
                ('brand_pic', models.CharField(max_length=256, verbose_name='\u54c1\u724c\u56fe\u7247', blank=True)),
                ('brand_post', models.CharField(max_length=256, verbose_name='\u54c1\u724c\u6d77\u62a5', blank=True)),
                ('brand_applink', models.CharField(max_length=256, verbose_name='\u54c1\u724cAPP\u534f\u8bae\u94fe\u63a5', blank=True)),
                ('start_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True)),
                ('order_val', models.IntegerField(default=0, verbose_name='\u6392\u5e8f\u503c')),
                ('is_active', models.BooleanField(default=True, verbose_name='\u4e0a\u7ebf')),
            ],
            options={
                'db_table': 'flashsale_brand_entry',
                'verbose_name': '\u7279\u5356/\u54c1\u724c\u63a8\u5e7f\u5165\u53e3',
                'verbose_name_plural': '\u7279\u5356/\u54c1\u724c\u63a8\u5e7f\u5165\u53e3',
            },
        ),
        migrations.CreateModel(
            name='BrandProduct',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('brand_name', models.CharField(db_index=True, max_length=32, verbose_name='\u54c1\u724c\u540d\u79f0', blank=True)),
                ('product_id', models.BigIntegerField(default=0, verbose_name='\u5546\u54c1id', db_index=True)),
                ('product_name', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u540d\u79f0', blank=True)),
                ('product_img', models.CharField(max_length=256, verbose_name='\u5546\u54c1\u56fe\u7247', blank=True)),
                ('start_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u5f00\u59cb\u65f6\u95f4', blank=True)),
                ('end_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True)),
                ('brand', models.ForeignKey(related_name='brand_products', verbose_name='\u54c1\u724c\u7f16\u53f7id', to='pay.BrandEntry')),
            ],
            options={
                'db_table': 'flashsale_brand_product',
                'verbose_name': '\u7279\u5356/\u54c1\u724c\u5546\u54c1',
                'verbose_name_plural': '\u7279\u5356/\u54c1\u724c\u5546\u54c1',
            },
        ),
        migrations.AddField(
            model_name='salerefund',
            name='amount_flow',
            field=jsonfield.fields.JSONField(default=b'{"desc":""}', max_length=512, verbose_name='\u9000\u6b3e\u53bb\u5411', blank=True),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='outer_id',
            field=models.CharField(max_length=32, verbose_name='\u5546\u54c1\u5916\u90e8\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='outer_sku_id',
            field=models.CharField(max_length=32, verbose_name='\u89c4\u683c\u5916\u90e8\u7f16\u7801', blank=True),
        ),
    ]
