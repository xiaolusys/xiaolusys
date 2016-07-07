# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0011_xiaolumm_addfield_other_model_choices'),
    ]

    operations = [
        migrations.CreateModel(
            name='PotentialMama',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('potential_mama', models.IntegerField(verbose_name='\u6f5c\u5728\u5988\u5988\u4e13\u5c5eid', db_index=True)),
                ('referal_mama', models.IntegerField(verbose_name='\u63a8\u8350\u4eba\u4e13\u5c5eid', db_index=True)),
                ('nick', models.CharField(max_length=32, verbose_name='\u6f5c\u5728\u5988\u5988\u6635\u79f0', blank=True)),
                ('thumbnail', models.CharField(max_length=256, verbose_name='\u6f5c\u5728\u5988\u5988\u5934\u50cf', blank=True)),
                ('uni_key', models.CharField(unique=True, max_length=32, verbose_name='\u552f\u4e00key')),
                ('is_full_member', models.BooleanField(default=False, verbose_name='\u662f\u5426\u8f6c\u6b63')),
            ],
            options={
                'db_table': 'xiaolumm_potential_record',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988/\u6f5c\u5728\u5c0f\u9e7f\u5988\u5988\u8868',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988/\u6f5c\u5728\u5c0f\u9e7f\u5988\u5988\u5217\u8868',
            },
        ),
    ]
