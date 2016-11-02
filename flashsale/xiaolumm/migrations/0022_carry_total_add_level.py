# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0021_carrytotal_add_activity_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrytotalrecord',
            name='agencylevel',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')]),
        ),
        migrations.AddField(
            model_name='carrytotalrecord',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='mamacarrytotal',
            name='agencylevel',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')]),
        ),
        migrations.AddField(
            model_name='mamateamcarrytotal',
            name='agencylevel',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')]),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='agencylevel',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')]),
        ),
        migrations.AddField(
            model_name='teamcarrytotalrecord',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='agencylevel',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u4ee3\u7406\u7c7b\u522b', choices=[(1, '\u666e\u901a'), (2, b'VIP1'), (3, 'A\u7c7b'), (12, b'VIP2'), (14, b'VIP4'), (16, b'VIP6'), (18, b'VIP8')]),
        ),
    ]
