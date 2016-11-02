# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import tagging.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0013_auto_20160531_1815'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='brandentry',
            options={'verbose_name': '\u7279\u5356/\u63a8\u5e7f\u4e13\u9898\u5165\u53e3', 'verbose_name_plural': '\u7279\u5356/\u63a8\u5e7f\u4e13\u9898\u5165\u53e3'},
        ),
        migrations.AlterModelOptions(
            name='brandproduct',
            options={'verbose_name': '\u7279\u5356/\u4e13\u9898\u5546\u54c1', 'verbose_name_plural': '\u7279\u5356/\u4e13\u9898\u5546\u54c1\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='modelproduct',
            name='tags',
            field=tagging.fields.TagField(max_length=255, null=True, verbose_name='\u6807\u7b7e', blank=True),
        ),
        migrations.AlterField(
            model_name='brandentry',
            name='brand_applink',
            field=models.CharField(max_length=256, verbose_name='\u4e13\u9898APP\u534f\u8bae\u94fe\u63a5', blank=True),
        ),
        migrations.AlterField(
            model_name='brandentry',
            name='brand_desc',
            field=models.TextField(max_length=512, verbose_name='\u4e13\u9898\u6d3b\u52a8\u63cf\u8ff0', blank=True),
        ),
        migrations.AlterField(
            model_name='brandentry',
            name='brand_name',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u4e13\u9898\u540d\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='brandentry',
            name='brand_pic',
            field=models.CharField(max_length=256, verbose_name='\u54c1\u724cLOGO', blank=True),
        ),
        migrations.AlterField(
            model_name='brandentry',
            name='brand_post',
            field=models.CharField(max_length=256, verbose_name='\u4e13\u9898\u6d77\u62a5', blank=True),
        ),
        migrations.AlterField(
            model_name='brandproduct',
            name='brand',
            field=models.ForeignKey(related_name='brand_products', verbose_name='\u6240\u5c5e\u4e13\u9898', to='pay.BrandEntry'),
        ),
        migrations.AlterField(
            model_name='brandproduct',
            name='brand_name',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u4e13\u9898\u540d\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='saleorder',
            name='refund_status',
            field=models.IntegerField(default=0, blank=True, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe7\x8a\xb6\xe6\x80\x81', choices=[(0, b'\xe6\xb2\xa1\xe6\x9c\x89\xe9\x80\x80\xe6\xac\xbe'), (3, b'\xe9\x80\x80\xe6\xac\xbe\xe5\xbe\x85\xe5\xae\xa1'), (4, b'\xe5\x90\x8c\xe6\x84\x8f\xe7\x94\xb3\xe8\xaf\xb7'), (5, b'\xe9\x80\x80\xe8\xb4\xa7\xe9\x80\x94\xe4\xb8\xad'), (2, b'\xe6\x8b\x92\xe7\xbb\x9d\xe9\x80\x80\xe6\xac\xbe'), (6, b'\xe7\xad\x89\xe5\xbe\x85\xe8\xbf\x94\xe6\xac\xbe'), (1, b'\xe9\x80\x80\xe6\xac\xbe\xe5\x85\xb3\xe9\x97\xad'), (7, b'\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f')]),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='status',
            field=models.IntegerField(default=3, blank=True, verbose_name=b'\xe9\x80\x80\xe6\xac\xbe\xe7\x8a\xb6\xe6\x80\x81', db_index=True, choices=[(0, b'\xe6\xb2\xa1\xe6\x9c\x89\xe9\x80\x80\xe6\xac\xbe'), (3, b'\xe9\x80\x80\xe6\xac\xbe\xe5\xbe\x85\xe5\xae\xa1'), (4, b'\xe5\x90\x8c\xe6\x84\x8f\xe7\x94\xb3\xe8\xaf\xb7'), (5, b'\xe9\x80\x80\xe8\xb4\xa7\xe9\x80\x94\xe4\xb8\xad'), (2, b'\xe6\x8b\x92\xe7\xbb\x9d\xe9\x80\x80\xe6\xac\xbe'), (6, b'\xe7\xad\x89\xe5\xbe\x85\xe8\xbf\x94\xe6\xac\xbe'), (1, b'\xe9\x80\x80\xe6\xac\xbe\xe5\x85\xb3\xe9\x97\xad'), (7, b'\xe9\x80\x80\xe6\xac\xbe\xe6\x88\x90\xe5\x8a\x9f')]),
        ),
    ]
