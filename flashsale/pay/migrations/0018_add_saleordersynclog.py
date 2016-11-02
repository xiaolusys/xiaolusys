# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0017_add_brandentry_brandproduct_pictype'),
    ]

    operations = [
        migrations.CreateModel(
            name='SaleOrderSyncLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('time_from', models.DateTimeField(verbose_name='\u5f00\u59cb\u65f6\u95f4')),
                ('time_to', models.DateTimeField(verbose_name='\u7ed3\u675f\u65f6\u95f4')),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name=b'UniKey')),
                ('target_num', models.IntegerField(default=0, null=True, verbose_name='\u76ee\u6807\u6570\u91cf')),
                ('actual_num', models.IntegerField(default=0, null=True, verbose_name='\u5b9e\u9645\u6570\u91cf')),
                ('type', models.IntegerField(default=0, db_index=True, verbose_name='\u7c7b\u578b', choices=[(0, '\u672a\u77e5'), (1, '\u53d1\u8d27'), (2, '\u8ba2\u8d27')])),
                ('status', models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u672a\u5b8c\u6210'), (2, '\u5b8c\u6210')])),
            ],
            options={
                'db_table': 'flashsale_saleorder_synclog',
                'verbose_name': 'v2/\u540c\u6b65\u68c0\u67e5\u65e5\u5fd7',
                'verbose_name_plural': 'v2/\u540c\u6b65\u68c0\u67e5\u65e5\u5fd7\u8868',
            },
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='has_good_change',
            field=models.BooleanField(default=False, verbose_name=b'\xe6\x9c\x89\xe6\x8d\xa2\xe8\xb4\xa7'),
        ),
        migrations.AlterField(
            model_name='salerefund',
            name='has_good_return',
            field=models.BooleanField(default=False, verbose_name=b'\xe6\x9c\x89\xe9\x80\x80\xe8\xb4\xa7'),
        ),
    ]
