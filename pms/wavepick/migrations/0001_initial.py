# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PickGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100, verbose_name='\u7ec4', blank=True)),
                ('wave_no', models.IntegerField(default=0, unique=True, verbose_name='\u6279\u53f7')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
            ],
            options={
                'db_table': 'supplychain_pick_group',
                'verbose_name': '\u6279\u53f7/\u7ec4',
                'verbose_name_plural': '\u6279\u53f7/\u7ec4\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PickItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wave_no', models.IntegerField(null=True, verbose_name='\u6279\u53f7', db_index=True)),
                ('out_sid', models.CharField(db_index=True, max_length=64, verbose_name='\u7269\u6d41\u7f16\u53f7', blank=True)),
                ('serial_no', models.IntegerField(null=True, verbose_name='\u5e8f\u53f7', db_index=True)),
                ('outer_sku_id', models.CharField(max_length=20, verbose_name='\u89c4\u683c\u5916\u90e8\u7f16\u7801', blank=True)),
                ('outer_id', models.CharField(max_length=64, verbose_name='\u5546\u54c1\u5916\u90e8\u7f16\u7801', blank=True)),
                ('barcode', models.CharField(db_index=True, max_length=64, verbose_name='\u8bc6\u522b\u7801', blank=True)),
                ('title', models.CharField(max_length=256, verbose_name='\u5546\u54c1\u540d\u79f0', blank=True)),
                ('item_num', models.IntegerField(default=0, verbose_name='\u6570\u91cf', db_index=True)),
                ('identity', models.IntegerField(default=0, verbose_name='\u5546\u54c1\u6807\u8bc6', db_index=True)),
            ],
            options={
                'db_table': 'supplychain_pick_item',
                'verbose_name': '\u6361\u8d27\u660e\u7ec6',
                'verbose_name_plural': '\u6361\u8d27\u660e\u7ec6\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='PickPublish',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('group_id', models.IntegerField(unique=True, verbose_name='\u7ec4\u53f7', db_index=True)),
                ('pvalue', models.CharField(default=b'000000000000000000000000', max_length=24, verbose_name='\u663e\u793a\u503c')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
            ],
            options={
                'db_table': 'supplychain_pick_publish',
                'verbose_name': '\u6361\u8d27LED\u503c',
                'verbose_name_plural': '\u6361\u8d27LED\u503c\u5217\u8868',
            },
        ),
        migrations.CreateModel(
            name='WavePick',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wave_no', models.IntegerField(verbose_name='\u6279\u53f7', db_index=True)),
                ('out_sid', models.CharField(max_length=64, verbose_name='\u7269\u6d41\u7f16\u53f7')),
                ('serial_no', models.IntegerField(verbose_name='\u5e8f\u53f7', db_index=True)),
                ('group_id', models.IntegerField(verbose_name='\u7ec4', db_index=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('status', models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u5206\u6361'), (1, '\u5206\u6361')])),
            ],
            options={
                'db_table': 'supplychain_pick_wave',
                'verbose_name': '\u6279\u53f7/\u7269\u6d41\u5355\u53f7',
                'verbose_name_plural': '\u6279\u53f7/\u7269\u6d41\u5355\u53f7',
            },
        ),
        migrations.AlterUniqueTogether(
            name='wavepick',
            unique_together=set([('wave_no', 'out_sid')]),
        ),
        migrations.AlterUniqueTogether(
            name='pickitem',
            unique_together=set([('out_sid', 'outer_id', 'outer_sku_id')]),
        ),
    ]
