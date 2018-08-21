# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0002_xiaoluswitch'),
    ]

    operations = [
        migrations.CreateModel(
            name='RenewRemind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('project_name', models.CharField(max_length=128, verbose_name='\u9879\u76ee\u540d\u79f0')),
                ('service_provider', models.CharField(max_length=128, verbose_name='\u63d0\u4f9b\u5546')),
                ('provider_phone', models.CharField(max_length=11, verbose_name='\u670d\u52a1\u4f9b\u5e94\u5546\u7535\u8bdd', blank=True)),
                ('start_service_time', models.DateTimeField(verbose_name='\u5f00\u59cb\u670d\u52a1\u65f6\u95f4', blank=True)),
                ('expire_time', models.DateTimeField(verbose_name='\u670d\u52a1\u5230\u671f\u65f6\u95f4')),
                ('describe', models.TextField(max_length=1024, verbose_name='\u670d\u52a1\u63cf\u8ff0', blank=True)),
                ('amount', models.FloatField(verbose_name='\u7eed\u8d39\u91d1\u989d')),
                ('principal', models.CharField(max_length=32, verbose_name='\u4e3b\u8981\u8d1f\u8d23\u4eba')),
                ('principal_phone', models.CharField(max_length=11, verbose_name='\u4e3b\u8981\u8d1f\u8d23\u4eba\u624b\u673a')),
                ('principal2_phone', models.CharField(max_length=11, verbose_name='\u7b2c2\u8d1f\u8d23\u4eba\u624b\u673a')),
                ('principal3_phone', models.CharField(max_length=11, verbose_name='\u7b2c3\u8d1f\u8d23\u4eba\u624b\u673a')),
                ('is_trace', models.BooleanField(default=True, db_index=True, verbose_name='\u662f\u5426\u8ffd\u8e2a')),
            ],
            options={
                'db_table': 'extrafunc_service_remind',
                'verbose_name': '\u7cfb\u7edf\u670d\u52a1/\u7eed\u8d39\u63d0\u9192\u8bb0\u5f55\u8868',
                'verbose_name_plural': '\u7cfb\u7edf\u670d\u52a1/\u7eed\u8d39\u63d0\u9192\u8bb0\u5f55\u5217\u8868',
            },
        ),
        migrations.AlterField(
            model_name='xiaoluswitch',
            name='status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u53d6\u6d88'), (1, '\u751f\u6548')]),
        ),
    ]
