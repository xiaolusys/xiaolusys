# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2017-02-11 16:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0033_auto_20170208_1813'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='packageskuitem',
            name='product',
        ),
        migrations.AlterField(
            model_name='dirtymergetrade',
            name='type',
            field=models.CharField(blank=True, choices=[(b'fixed', '\u6dd8\u5b9d&\u5546\u57ce'), (b'fenxiao', '\u6dd8\u5b9d\u5206\u9500'), (b'sale', '\u5c0f\u9e7f\u7279\u5356'), (b'jd', '\u4eac\u4e1c\u5546\u57ce'), (b'yhd', '\u4e00\u53f7\u5e97'), (b'dd', '\u5f53\u5f53\u5546\u57ce'), (b'sn', '\u82cf\u5b81\u6613\u8d2d'), (b'wx', '\u5fae\u4fe1\u5c0f\u5e97'), (b'amz', '\u4e9a\u9a6c\u900a'), (b'direct', '\u5185\u552e'), (b'reissue', '\u8865\u53d1'), (b'exchange', '\u9000\u6362\u8d27'), (b'exchange', '\u5c0f\u9e7f\u7279\u5356'), (b'exchange', '\u9000\u6362\u8d27')], db_index=True, max_length=32, verbose_name='\u8ba2\u5355\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='mergetrade',
            name='type',
            field=models.CharField(blank=True, choices=[(b'fixed', '\u6dd8\u5b9d&\u5546\u57ce'), (b'fenxiao', '\u6dd8\u5b9d\u5206\u9500'), (b'sale', '\u5c0f\u9e7f\u7279\u5356'), (b'jd', '\u4eac\u4e1c\u5546\u57ce'), (b'yhd', '\u4e00\u53f7\u5e97'), (b'dd', '\u5f53\u5f53\u5546\u57ce'), (b'sn', '\u82cf\u5b81\u6613\u8d2d'), (b'wx', '\u5fae\u4fe1\u5c0f\u5e97'), (b'amz', '\u4e9a\u9a6c\u900a'), (b'direct', '\u5185\u552e'), (b'reissue', '\u8865\u53d1'), (b'exchange', '\u9000\u6362\u8d27'), (b'exchange', '\u5c0f\u9e7f\u7279\u5356'), (b'exchange', '\u9000\u6362\u8d27')], db_index=True, max_length=32, verbose_name='\u8ba2\u5355\u7c7b\u578b'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='buyer_id',
            field=models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name='\u4e70\u5bb6ID'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='user_address_id',
            field=models.CharField(blank=True, db_index=True, max_length=40, verbose_name='\u5730\u5740ID'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='weighter',
            field=models.CharField(blank=True, help_text='\u6216\u8005\u7b2c\u4e09\u65b9\u53d1\u8d27\u7684\u5bfc\u5165\u8005', max_length=64, verbose_name='\u79f0\u91cd\u5458'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='assign_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u5907\u8d27\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='pay_time',
            field=models.DateTimeField(db_index=True, help_text='\u4ed8\u6b3e\u65f6\u95f4|\u5929\u732b\u6210\u4ea4\u65f6\u95f4|\u9000\u8d27\u5ba1\u6838\u65f6\u95f4|\u8be5\u65f6\u95f4\u51b3\u5b9a\u53d1\u8d27\u987a\u5e8f', verbose_name='\u4ed8\u6b3e\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='packagestat',
            name='num',
            field=models.IntegerField(default=0, help_text='\u6ce8\u610f\u8fd9\u91cc\u5305\u542b\u4e86\u5220\u9664\u5305\u88f9\u6570', verbose_name='\u5df2\u5904\u7406\u5305\u88f9\u6570'),
        ),
    ]