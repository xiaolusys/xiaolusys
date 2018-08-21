# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('items', '0016_rename_productskustat_to_skustock'),
    ]

    operations = [
        migrations.AddField(
            model_name='skustock',
            name='paid_num',
            field=models.IntegerField(default=0, verbose_name='\u4ed8\u6b3e\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_assigned_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u5408\u5355\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_finish_num',
            field=models.IntegerField(default=0, verbose_name='\u5b8c\u6210\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_merged_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u6253\u5355\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_paid_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u5904\u7406\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_prepare_book_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u8ba2\u8d27\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_ready_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u5206\u914d\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_sent_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u7b7e\u6536\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_waitpost_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u79f0\u91cd\u6570'),
        ),
        migrations.AddField(
            model_name='skustock',
            name='psi_waitscan_num',
            field=models.IntegerField(default=0, verbose_name='\u5f85\u626b\u63cf\u6570'),
        ),
        migrations.AlterField(
            model_name='skustock',
            name='assign_num',
            field=models.IntegerField(default=0, verbose_name='\u5df2\u5206\u914d\u6570'),
        ),
    ]
