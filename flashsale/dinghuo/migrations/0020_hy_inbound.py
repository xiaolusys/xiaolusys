# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0019_change_status_choices'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inbound',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(0, '\u4f5c\u5e9f'), (1, '\u5f85\u5904\u7406'), (2, '\u7b49\u5f85\u8d28\u68c0'), (3, '\u5b8c\u6210')]),
        ),
        migrations.AddField(
            model_name='inbound',
            name='ori_orderlist_id',
            field=models.CharField(default=b'', max_length=32, verbose_name='\u8ba2\u8d27\u5355\u53f7'),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='express_no',
            field=models.CharField(max_length=32, verbose_name='\u5feb\u9012\u5355\u53f7'),
        ),
        migrations.AlterField(
            model_name='inbounddetail',
            name='status',
            field=models.SmallIntegerField(default=2, verbose_name='\u72b6\u6001', choices=[(1, '\u8d28\u68c0\u901a\u8fc7'), (2, '\u672a\u8d28\u68c0')]),
        ),
        migrations.AddField(
            model_name='inbound',
            name='checked',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u8d28\u68c0'),
        ),
        migrations.AddField(
            model_name='inbound',
            name='out_stock',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u591a\u8d27'),
        ),
        migrations.AddField(
            model_name='inbound',
            name='wrong',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u6709\u9519'),
        ),
        migrations.AddField(
            model_name='inbounddetail',
            name='checked',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u68c0\u67e5'),
        ),
        migrations.AddField(
            model_name='inbounddetail',
            name='out_stock',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u591a\u8d27'),
        ),
        migrations.AddField(
            model_name='inbounddetail',
            name='wrong',
            field=models.BooleanField(default=False, verbose_name='\u662f\u5426\u6709\u9519'),
        ),
        migrations.AlterField(
            model_name='inbound',
            name='status',
            field=models.SmallIntegerField(default=0, verbose_name='\u8fdb\u5ea6', choices=[(9, '\u4f5c\u5e9f'), (0, '\u521d\u59cb'), (1, '\u5f85\u5206\u914d'), (2, '\u7b49\u5f85\u8d28\u68c0'), (3, '\u5b8c\u6210')]),
        ),
        migrations.AlterField(
            model_name='inbounddetail',
            name='status',
            field=models.SmallIntegerField(default=2, verbose_name='\u72b6\u6001', choices=[(1, '\u6b63\u5e38'), (2, '\u6709\u95ee\u9898')]),
        ),
    ]
