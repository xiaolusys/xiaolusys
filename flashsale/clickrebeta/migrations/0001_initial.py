# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='OrderDetailRebeta',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('detail_id', models.CharField(max_length=64, verbose_name='\u8ba2\u5355\u660e\u7ec6ID', db_index=True)),
                ('scheme_id', models.IntegerField(default=0, verbose_name='\u4f63\u91d1\u8ba1\u5212ID')),
                ('pay_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u652f\u4ed8\u65f6\u95f4', blank=True)),
                ('order_amount', models.IntegerField(default=0, verbose_name='\u652f\u4ed8\u91d1\u989d')),
                ('rebeta_amount', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u63d0\u6210')),
                ('status', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u72b6\u6001', choices=[(0, '\u5df2\u4ed8\u6b3e'), (1, '\u5df2\u5b8c\u6210'), (2, '\u5df2\u9000\u6b3e')])),
            ],
            options={
                'db_table': 'flashsale_tongji_orderebeta',
                'verbose_name': '\u8ba2\u5355\u4f63\u91d1\u660e\u7ec6',
                'verbose_name_plural': '\u8ba2\u5355\u4f63\u91d1\u660e\u7ec6',
            },
        ),
        migrations.CreateModel(
            name='StatisticsShopping',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('linkid', models.IntegerField(default=0, verbose_name='\u5988\u5988ID')),
                ('linkname', models.CharField(default=b'', max_length=20, verbose_name='\u4ee3\u7406\u4eba')),
                ('openid', models.CharField(db_index=True, max_length=64, verbose_name='\u6536\u8d27\u624b\u673a', blank=True)),
                ('wxorderid', models.CharField(max_length=64, verbose_name='\u5fae\u4fe1\u8ba2\u5355', db_index=True)),
                ('wxordernick', models.CharField(max_length=32, verbose_name='\u8d2d\u4e70\u6635\u79f0')),
                ('wxorderamount', models.IntegerField(default=0, verbose_name='\u5fae\u4fe1\u8ba2\u5355\u4ef7\u683c')),
                ('rebetamount', models.IntegerField(default=0, verbose_name='\u6709\u6548\u91d1\u989d')),
                ('tichengcount', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u63d0\u6210')),
                ('shoptime', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u63d0\u6210\u65f6\u95f4', db_index=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u72b6\u6001', choices=[(0, '\u5df2\u4ed8\u6b3e'), (1, '\u5df2\u5b8c\u6210'), (2, '\u5df2\u53d6\u6d88')])),
            ],
            options={
                'db_table': 'flashsale_tongji_shopping',
                'verbose_name': '\u7edf\u8ba1\u8d2d\u4e70',
                'verbose_name_plural': '\u7edf\u8ba1\u8d2d\u4e70\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='StatisticsShoppingByDay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('linkid', models.IntegerField(default=0, verbose_name='\u94fe\u63a5ID')),
                ('linkname', models.CharField(default=b'', max_length=20, verbose_name='\u4ee3\u7406\u4eba')),
                ('buyercount', models.IntegerField(default=0, verbose_name='\u8d2d\u4e70\u4eba\u6570')),
                ('ordernumcount', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u603b\u6570')),
                ('orderamountcount', models.IntegerField(default=0, verbose_name='\u8ba2\u5355\u603b\u4ef7')),
                ('todayamountcount', models.IntegerField(default=0, verbose_name='\u63d0\u6210\u603b\u6570')),
                ('tongjidate', models.DateField(verbose_name='\u7edf\u8ba1\u7684\u65e5\u671f', db_index=True)),
            ],
            options={
                'db_table': 'flashsale_tongji_shopping_day',
                'verbose_name': '\u7edf\u8ba1\u8d2d\u4e70(\u6309\u5929)',
                'verbose_name_plural': '\u7edf\u8ba1\u8d2d\u4e70(\u6309\u5929)\u5217\u8868',
            },
        ),
        migrations.AlterUniqueTogether(
            name='statisticsshoppingbyday',
            unique_together=set([('linkid', 'tongjidate')]),
        ),
        migrations.AlterUniqueTogether(
            name='statisticsshopping',
            unique_together=set([('linkid', 'wxorderid')]),
        ),
        migrations.AddField(
            model_name='orderdetailrebeta',
            name='order',
            field=models.ForeignKey(related_name='detail_orders', verbose_name=b'\xe8\xae\xa2\xe5\x8d\x95', to='clickrebeta.StatisticsShopping', null=True),
        ),
        migrations.AlterUniqueTogether(
            name='orderdetailrebeta',
            unique_together=set([('order', 'detail_id')]),
        ),
    ]
