# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0034_auto_20160813_0026'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaDailyAppVisit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('mama_id', models.IntegerField(default=0, verbose_name='\u5988\u5988id', db_index=True)),
                ('uni_key', models.CharField(unique=True, max_length=128, verbose_name='\u552f\u4e00ID', blank=True)),
                ('date_field', models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True)),
            ],
            options={
                'db_table': 'flashsale_xlmm_mamadailyappvisit',
                'verbose_name': 'V2/\u5988\u5988app\u8bbf\u95ee',
                'verbose_name_plural': 'V2/\u5988\u5988app\u8bbf\u95ee\u5217\u8868',
            },
        ),
    ]
