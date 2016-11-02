# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0053_rank_activity_member_ids'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='xiaolumama',
            name='user_group',
        ),
        migrations.AddField(
            model_name='mamadailyappvisit',
            name='num_visits',
            field=models.IntegerField(default=1, verbose_name='\u8bbf\u95ee\u6b21\u6570'),
        ),
        migrations.AddField(
            model_name='mamadailyappvisit',
            name='renew_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u5988\u5988\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='mamadevicestats',
            name='num_visits',
            field=models.IntegerField(default=0, verbose_name='\u8bbf\u95ee\u6b21\u6570'),
        ),
        migrations.AddField(
            model_name='mamadevicestats',
            name='renew_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u5988\u5988\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='xiaolumama',
            name='user_group_id',
            field=models.IntegerField(null=True, verbose_name='\u5206\u7ec4'),
        ),
    ]
