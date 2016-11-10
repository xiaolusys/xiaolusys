# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0021_add_field_reason'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='packageskuitem',
            options={'verbose_name': '\u5305\u88f9\u5546\u54c1', 'verbose_name_plural': '\u5305\u88f9\u5546\u54c1\u5217\u8868'},
        ),
        migrations.RemoveField(
            model_name='packageorder',
            name='merged',
        ),
        migrations.RemoveField(
            model_name='packageorder',
            name='type',
        ),
        migrations.RemoveField(
            model_name='packageskuitem',
            name='book_time',
        ),
        migrations.RemoveField(
            model_name='packageskuitem',
            name='gift_type',
        ),
        migrations.AddField(
            model_name='packageorder',
            name='can_send_time',
            field=models.DateTimeField(null=True, verbose_name='\u53ef\u53d1\u8d27\u65f6\u95f4', db_column=b'merged', blank=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='booked_time',
            field=models.DateTimeField(null=True, verbose_name='\u8ba2\u4e0b\u8d27\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='merge_time',
            field=models.DateTimeField(null=True, verbose_name='\u5408\u5355\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='prepare_book_time',
            field=models.DateTimeField(null=True, verbose_name='\u51c6\u5907\u8ba2\u8d27\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='ready_time',
            field=models.DateTimeField(null=True, verbose_name='\u5206\u914d\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='scan_time',
            field=models.DateTimeField(null=True, verbose_name='\u626b\u63cf\u65f6\u95f4', db_index=True),
        ),
        migrations.AddField(
            model_name='packageskuitem',
            name='weight_time',
            field=models.DateTimeField(null=True, verbose_name='\u79f0\u91cd\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='dirtymergetrade',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='mergetrade',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='priority',
            field=models.IntegerField(default=0, verbose_name='\u4f5c\u5e9f\u5b57\u6bb5'),
        ),
        migrations.AlterField(
            model_name='packageorder',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='assign_status',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u5907\u8d27'), (1, '\u5df2\u5907\u8d27'), (2, '\u5df2\u51fa\u8d27'), (4, '\u5382\u5bb6\u5907\u8d27\u4e2d'), (3, '\u5df2\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='status',
            field=models.CharField(default=b'paid', choices=[(b'paid', '\u521a\u4ed8\u5f85\u5904\u7406'), (b'prepare_book', '\u5f85\u8ba2\u8d27'), (b'booked', '\u5f85\u5907\u8d27'), (b'ready', '\u5f85\u5206\u914d'), (b'assigned', '\u5f85\u5408\u5355'), (b'merged', '\u5f85\u6253\u5355'), (b'waitscan', '\u5f85\u626b\u63cf'), (b'waitpost', '\u5f85\u79f0\u91cd'), (b'sent', '\u5f85\u6536\u8d27'), (b'finish', '\u5b8c\u6210'), (b'cancel', '\u53d6\u6d88'), (b'holding', '\u6302\u8d77')], max_length=32, blank=True, verbose_name='\u8ba2\u5355\u72b6\u6001', db_index=True),
        ),
        migrations.AlterField(
            model_name='packageskuitem',
            name='ware_by',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u6240\u5c5e\u4ed3\u5e93', choices=[(0, '\u672a\u9009\u4ed3'), (1, '\u4e0a\u6d77\u4ed3'), (2, '\u5e7f\u5dde\u4ed3'), (3, '\u516c\u53f8\u4ed3'), (9, '\u7b2c\u4e09\u65b9\u4ed3')]),
        ),
    ]
