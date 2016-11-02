# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mmexam', '0005_mamaexam_add_participant'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExamResultDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('customer_id', models.BigIntegerField(verbose_name='\u7528\u6237ID', db_index=True)),
                ('sheaves', models.IntegerField(default=0, verbose_name='\u8003\u8bd5\u8f6e\u6570', db_index=True)),
                ('question_id', models.BigIntegerField(verbose_name='\u9898\u53f7', db_index=True)),
                ('answer', models.CharField(max_length=32, verbose_name='\u7528\u6237\u56de\u7b54')),
                ('is_right', models.BooleanField(default=False, verbose_name='\u662f\u5426\u6b63\u786e')),
                ('point', models.FloatField(default=0.0, verbose_name='\u5206\u503c')),
                ('uni_key', models.CharField(max_length=64, verbose_name='\u552f\u4e00\u6807\u8bc6')),
            ],
            options={
                'db_table': 'flashsale_mmexam_result_detail',
                'verbose_name': '\u4ee3\u7406\u8003\u8bd5\u7ed3\u679c\u660e\u7ec6',
                'verbose_name_plural': '\u4ee3\u7406\u8003\u8bd5\u7ed3\u679c\u660e\u7ec6\u5217\u8868',
            },
        ),
    ]
