# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dinghuo', '0038_add_field_rgdetail_wrong_desc'),
    ]

    operations = [
        migrations.CreateModel(
            name='PackageBackOrderStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('day_date', models.DateField(verbose_name='\u7edf\u8ba1\u65e5\u671f')),
                ('three_backorder_num', models.IntegerField(default=0, verbose_name='3\u5929\u672a\u53d1\u8d27\u8ba2\u5355\u6570')),
                ('five_backorder_num', models.IntegerField(default=0, verbose_name='5\u5929\u672a\u53d1\u8d27\u8ba2\u5355\u6570')),
                ('fifteen_backorder_num', models.IntegerField(default=0, verbose_name='1\uff15\u5929\u672a\u53d1\u8d27\u8ba2\u5355\u6570')),
                ('backorder_ids', models.TextField(null=True, verbose_name='3\u5929\u672a\u53d1\u8d27\u8ba2\u5355ID', blank=True)),
                ('purchaser', models.ForeignKey(verbose_name='\u91c7\u8d2d\u5458', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'flashsale_dinghuo_backorderstats',
                'verbose_name': '\u5ef6\u65f6\u53d1\u8d27\u8ba2\u5355\u7edf\u8ba1',
                'verbose_name_plural': '\u5ef6\u65f6\u53d1\u8d27\u8ba2\u5355\u7edf\u8ba1\u5217\u8868',
            },
        ),
        migrations.AlterField(
            model_name='inbound',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='orderlist',
            name='sys_status',
            field=models.CharField(default=b'draft', max_length=16, verbose_name='\u7cfb\u7edf\u72b6\u6001', db_index=True, choices=[(b'draft', '\u8349\u7a3f'), (b'approval', '\u5df2\u5ba1\u6838'), (b'billing', '\u7ed3\u7b97\u4e2d'), (b'finished', '\u5df2\u5b8c\u6210'), (b'close', '\u5df2\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='unreturnsku',
            name='sale_product',
            field=models.ForeignKey(verbose_name='\u5173\u8054\u9009\u54c1', to='supplier.SaleProduct', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='packagebackorderstats',
            unique_together=set([('day_date', 'purchaser')]),
        ),
    ]
