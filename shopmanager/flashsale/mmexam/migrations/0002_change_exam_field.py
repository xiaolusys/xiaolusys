# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mmexam', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='pub_date',
        ),
        migrations.RemoveField(
            model_name='question',
            name='single_many',
        ),
        migrations.AddField(
            model_name='question',
            name='expire_time',
            field=models.DateTimeField(null=True, verbose_name='\u8003\u8bd5\u622a\u6b62\u65e5\u671f', db_index=True),
        ),
        migrations.AddField(
            model_name='question',
            name='question_types',
            field=models.IntegerField(default=1, verbose_name='\u9898\u578b', choices=[(1, '\u5355\u9009'), (2, '\u591a\u9009'), (3, '\u5bf9\u9519\u9898')]),
        ),
        migrations.AddField(
            model_name='question',
            name='score',
            field=models.IntegerField(default=0, verbose_name='\u5206\u503c'),
        ),
        migrations.AddField(
            model_name='question',
            name='sheaves',
            field=models.IntegerField(default=0, verbose_name='\u8003\u8bd5\u8f6e\u6570', db_index=True),
        ),
        migrations.AddField(
            model_name='question',
            name='start_time',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='\u8003\u8bd5\u5f00\u59cb\u65e5\u671f', db_index=True),
        ),
        migrations.AddField(
            model_name='result',
            name='customer_id',
            field=models.BigIntegerField(default=0, verbose_name='\u7528\u6237id', db_index=True),
        ),
        migrations.AddField(
            model_name='result',
            name='sheaves',
            field=models.IntegerField(default=0, verbose_name='\u8003\u8bd5\u8f6e\u6570', db_index=True),
        ),
        migrations.AddField(
            model_name='result',
            name='total_point',
            field=models.FloatField(default=0.0, verbose_name='\u603b\u5206'),
        ),
        migrations.AddField(
            model_name='result',
            name='xlmm_id',
            field=models.IntegerField(default=0, verbose_name='\u5988\u5988id', db_index=True),
        ),
    ]
