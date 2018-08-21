# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0006_auto_20160517_1845'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='returngoods',
            options={'verbose_name': '\u4ed3\u5e93\u9000\u8d27\u5355', 'verbose_name_plural': '\u4ed3\u5e93\u9000\u8d27\u5355\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='returngoods',
            name='confirm_pic_url',
            field=models.URLField(verbose_name='\u4ed8\u6b3e\u622a\u56fe', blank=True),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='confirm_refund',
            field=models.BooleanField(default=False, verbose_name='\u9000\u6b3e\u989d\u786e\u8ba4'),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='logistics_company_id',
            field=models.BigIntegerField(null=True, verbose_name=b'\xe7\x89\xa9\xe6\xb5\x81\xe5\x85\xac\xe5\x8f\xb8ID'),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='refund_confirmer_id',
            field=models.IntegerField(default=None, null=True, verbose_name='\u9000\u6b3e\u989d\u786e\u8ba4\u4eba'),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='refund_fee',
            field=models.FloatField(default=0.0, verbose_name='\u5ba2\u6237\u9000\u6b3e\u989d'),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='refund_status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u9000\u6b3e\u72b6\u6001', choices=[(0, '\u672a\u4ed8'), (1, '\u5df2\u5b8c\u6210'), (2, '\u90e8\u5206\u652f\u4ed8'), (3, '\u5df2\u5173\u95ed')]),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='transaction_number',
            field=models.CharField(default=b'', max_length=64, verbose_name='\u4ea4\u6613\u5355\u53f7'),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='transactor_id',
            field=models.IntegerField(default=None, null=True, verbose_name='\u5904\u7406\u4ebaid', db_index=True),
        ),
        migrations.AddField(
            model_name='returngoods',
            name='upload_time',
            field=models.DateTimeField(null=True, verbose_name='\u4e0a\u4f20\u622a\u56fe\u65f6\u95f4'),
        ),
        migrations.AlterField(
            model_name='inbounddetail',
            name='status',
            field=models.SmallIntegerField(default=2, verbose_name='\u72b6\u6001', choices=[(1, '\u5df2\u5206\u914d'), (2, '\u672a\u5206\u914d')]),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='noter',
            field=models.CharField(max_length=32, verbose_name='\u5f55\u5165\u4eba'),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='product_id',
            field=models.BigIntegerField(default=0, verbose_name='\u9000\u8d27\u5546\u54c1id', db_index=True),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='return_num',
            field=models.IntegerField(default=0, verbose_name='\u9000\u4ef6\u603b\u6570'),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='sid',
            field=models.CharField(max_length=64, null=True, verbose_name='\u53d1\u8d27\u7269\u6d41\u5355\u53f7', blank=True),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u65b0\u5efa'), (1, '\u5df2\u5ba1\u6838'), (2, '\u5df2\u4f5c\u5e9f'), (3, '\u5df2\u53d1\u8d27'), (31, '\u5f85\u9a8c\u9000\u6b3e'), (4, '\u9000\u8d27\u6210\u529f'), (5, '\u9000\u8d27\u5931\u8d25')]),
        ),
        migrations.AlterField(
            model_name='returngoods',
            name='sum_amount',
            field=models.FloatField(default=0.0, verbose_name='\u9000\u6b3e\u603b\u989d'),
        ),
    ]
