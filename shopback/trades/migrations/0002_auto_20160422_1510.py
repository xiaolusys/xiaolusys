# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='packageorder',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True),
        ),
        migrations.AlterField(
            model_name='mergeorder',
            name='num',
            field=models.IntegerField(default=0, verbose_name='\u6570\u91cf'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='seller_id',
            field=models.BigIntegerField(verbose_name='\u5356\u5bb6ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='num',
            field=models.IntegerField(default=0, verbose_name='\u6570\u91cf'),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='outer_id',
            field=models.CharField(max_length=20, verbose_name='\u5546\u54c1\u7f16\u7801', blank=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='package_order_id',
            field=models.CharField(db_index=True, max_length=100, null=True, verbose_name='\u5305\u88f9\u5355ID', blank=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='sku_id',
            field=models.CharField(db_index=True, max_length=20, verbose_name='SKUID', blank=True),
        ),
    ]
