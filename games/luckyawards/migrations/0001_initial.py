# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Joiner',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, verbose_name='\u59d3\u540d')),
                ('thumbnail', models.ImageField(upload_to=b'site_media/media', max_length=256, verbose_name='\u7167\u7247')),
                ('born_at', models.DateField(null=True, verbose_name='\u51fa\u751f\u5e74\u6708', blank=True)),
                ('addresss', models.CharField(max_length=64, verbose_name='\u5730\u5740', blank=True)),
                ('descript', models.CharField(max_length=128, verbose_name='\u8bf4\u660e', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True)),
                ('is_active', models.BooleanField(default=True, verbose_name='\u662f\u5426\u6709\u6548')),
            ],
            options={
                'db_table': 'game_joiner',
                'verbose_name': '\u6d3b\u52a8\u62bd\u5956',
                'verbose_name_plural': '\u6d3b\u52a8\u62bd\u5956\u4eba\u5458\u5217\u8868',
            },
        ),
    ]
