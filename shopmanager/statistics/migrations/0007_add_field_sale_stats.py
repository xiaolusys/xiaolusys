# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('statistics', '0006_change_table_name'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='productstockstat',
            options={'verbose_name': '\u5e93\u5b58\u7edf\u8ba1\u8868', 'verbose_name_plural': '\u5e93\u5b58\u7edf\u8ba1\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='salestats',
            name='timely_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u65f6\u95f4\u7ef4\u5ea6\u7c7b\u578b', choices=[(0, '\u65e5\u62a5\u7ec6\u5206'), (1, '\u65e5\u62a5'), (2, '\u5468\u62a5'), (3, '\u6708\u62a5'), (4, '\u5b63\u62a5'), (5, '\u5e74\u62a5')]),
        ),
        migrations.AlterField(
            model_name='productstockstat',
            name='record_type',
            field=models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'), (17, '\u6bcf\u65e5\u5feb\u7167'), (20, '\u805a\u5408')]),
        ),
        migrations.AlterField(
            model_name='salestats',
            name='record_type',
            field=models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b', choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'), (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'), (17, '\u6bcf\u65e5\u5feb\u7167'), (20, '\u805a\u5408')]),
        ),
    ]
