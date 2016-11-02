# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('statistics', '0007_add_field_sale_stats'),
    ]

    operations = [
        migrations.AddField(
            model_name='productstockstat',
            name='timely_type',
            field=models.IntegerField(default=6, db_index=True, verbose_name='\u65f6\u95f4\u7ef4\u5ea6\u7c7b\u578b',
                                      choices=[(6, '\u65e5\u62a5'), (7, '\u5468\u62a5'), (8, '\u6708\u62a5'),
                                               (9, '\u5b63\u62a5'), (10, '\u5e74\u62a5')]),
        ),
        migrations.AlterField(
            model_name='productstockstat',
            name='record_type',
            field=models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b',
                                      choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'),
                                               (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'),
                                               (16, '\u603b\u8ba1'), (17, '\u6bcf\u65e5\u5feb\u7167')]),
        ),
        migrations.AlterField(
            model_name='salestats',
            name='record_type',
            field=models.IntegerField(db_index=True, verbose_name='\u8bb0\u5f55\u7c7b\u578b',
                                      choices=[(1, 'SKU\u7ea7'), (4, '\u989c\u8272\u7ea7'), (7, '\u6b3e\u5f0f\u7ea7'),
                                               (13, '\u4f9b\u5e94\u5546\u7ea7'), (14, '\u4e70\u624bBD\u7ea7'),
                                               (16, '\u603b\u8ba1'), (17, '\u6bcf\u65e5\u5feb\u7167')]),
        ),
        migrations.AlterField(
            model_name='salestats',
            name='timely_type',
            field=models.IntegerField(default=6, db_index=True, verbose_name='\u65f6\u95f4\u7ef4\u5ea6\u7c7b\u578b',
                                      choices=[(6, '\u65e5\u62a5'), (7, '\u5468\u62a5'), (8, '\u6708\u62a5'),
                                               (9, '\u5b63\u62a5'), (10, '\u5e74\u62a5')]),
        ),
    ]
