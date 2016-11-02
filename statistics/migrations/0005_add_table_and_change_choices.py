# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0004_alter_paytime'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductStockStat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('parent_id', models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u4e0a\u4e00\u7ea7id', blank=True)),
                ('current_id', models.CharField(db_index=True, max_length=32, null=True, verbose_name='\u7ea7\u522b\u5bf9\u5e94instance_id', blank=True)),
                ('date_field', models.DateField(verbose_name='\u65e5\u671f', db_index=True)),
                ('name', models.CharField(max_length=64, null=True, verbose_name='\u63cf\u8ff0')),
                ('pic_path', models.CharField(max_length=256, null=True, verbose_name='\u56fe\u7247')),
                ('quantity', models.IntegerField(default=0, verbose_name='\u5e93\u5b58\u6570\u91cf')),
                ('sku_inferior_num', models.IntegerField(default=0, verbose_name='\u6b21\u54c1\u6570\u91cf')),
                ('amount', models.FloatField(default=0, verbose_name='\u5e93\u5b58\u91d1\u989d')),
                ('uni_key', models.CharField(unique=True, max_length=64, verbose_name='\u552f\u4e00\u6807\u8bc6')),
                ('record_type', models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'), (16, '\u65e5\u671f\u7ea7'), (17, '\u65e5\u671f\u7ea7\u5feb\u7167'), (18, '\u5468\u62a5\u544a'), (19, '\u6708\u62a5\u544a'), (20, '\u5b63\u5ea6\u62a5\u544a')])),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='salestats',
            name='record_type',
            field=models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'), (16, '\u65e5\u671f\u7ea7'), (17, '\u65e5\u671f\u7ea7\u5feb\u7167'), (18, '\u5468\u62a5\u544a'), (19, '\u6708\u62a5\u544a'), (20, '\u5b63\u5ea6\u62a5\u544a')]),
        ),
    ]
