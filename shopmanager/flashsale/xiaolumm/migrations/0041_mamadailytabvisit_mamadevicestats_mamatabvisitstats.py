# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0040_add_index_to_device_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaDailyTabVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(default=0, verbose_name='\u5988\u5988id', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('date_field', models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True)),
                ('stats_tab', models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868')])),
            ],
            options={
                'db_table': 'flashsale_xlmm_mamadailytabvisit',
                'verbose_name': 'V2/\u5988\u5988tab\u8bbf\u95ee\u8bb0\u5f55',
                'verbose_name_plural': 'V2/\u5988\u5988tab\u8bbf\u95ee\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='MamaDeviceStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('device_type', models.IntegerField(default=0, db_index=True, verbose_name='\u8bbe\u5907', choices=[(0, b'Unknown'), (1, b'Android'), (2, b'IOS')])),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('date_field', models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True)),
                ('num_latest', models.IntegerField(default=0, verbose_name='\u6700\u65b0\u7248\u672c\u6570')),
                ('num_outdated', models.IntegerField(default=0, verbose_name='\u65e7\u7248\u672c\u6570')),
            ],
            options={
                'db_table': 'flashsale_xlmm_mamadevicestats',
                'verbose_name': 'V2/\u5988\u5988\u8bbe\u5907\u7edf\u8ba1',
                'verbose_name_plural': 'V2/\u5988\u5988\u8bbe\u5907\u7edf\u8ba1\u8868',
            },
        ),
        migrations.CreateModel(
            name='MamaTabVisitStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('stats_tab', models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868')])),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('date_field', models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True)),
                ('visit_total', models.IntegerField(default=0, verbose_name='\u8bbf\u95ee\u6b21\u6570')),
            ],
            options={
                'db_table': 'flashsale_xlmm_mamatabvisitstats',
                'verbose_name': 'V2/\u5988\u5988tab\u8bbf\u95ee\u7edf\u8ba1',
                'verbose_name_plural': 'V2/\u5988\u5988tab\u8bbf\u95ee\u7edf\u8ba1\u8868',
            },
        ),
    ]
