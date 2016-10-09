# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='STOThermal',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('waybill_code', models.CharField(unique=True, max_length=32, verbose_name='STO\u8fd0\u5355\u53f7')),
                ('print_data', models.TextField(max_length=5120, verbose_name='\u70ed\u654f\u6253\u5370\u4fe1\u606f')),
                ('object_id', models.CharField(max_length=32, verbose_name=b'object_id', blank=True)),
                ('create_time', models.DateTimeField(default=datetime.datetime.now, verbose_name='\u521b\u5efa\u65f6\u95f4')),
                ('operation_user', models.ForeignKey(related_name='STO_thermal', verbose_name='\u64cd\u4f5c\u4eba', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'flashsale_STOthermal',
                'verbose_name': '\u7533\u901a\u70ed\u654f\u5355',
                'verbose_name_plural': '\u7533\u901a\u70ed\u654f\u5217\u8868',
            },
        ),
    ]
