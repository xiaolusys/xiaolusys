# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0054_add_renew_type_num_visits'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamamissionrecord',
            name='award_amount',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1(\u5206)'),
        ),
        migrations.AddField(
            model_name='mamamissionrecord',
            name='target_value',
            field=models.IntegerField(default=0, verbose_name='\u76ee\u6807\u503c'),
        ),
        migrations.AlterField(
            model_name='activitymamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='activitymamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u63a8\u8350\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u65b0\u624b\u4efb\u52a1'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u63a8\u8350\u65b0\u624b\u4efb\u52a1'), (7, '\u4e00\u5143\u9080\u8bf7'), (8, '\u5173\u6ce8\u516c\u4f17\u53f7'), (9, '\u9500\u552e\u5956\u52b1'), (10, '\u56e2\u961f\u9500\u552e\u5956\u52b1')]),
        ),
        migrations.AlterField(
            model_name='carrytotalrecord',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='grouprelationship',
            name='referal_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='mamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='mamadailyappvisit',
            name='device_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u8bbe\u5907', choices=[(0, b'Unknown'), (1, b'Android'), (2, b'IOS'), (3, b'\xe6\xb5\x8f\xe8\xa7\x88\xe5\x99\xa8')]),
        ),
        migrations.AlterField(
            model_name='mamadailyappvisit',
            name='renew_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u5988\u5988\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='mamadevicestats',
            name='device_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u8bbe\u5907', choices=[(0, b'Unknown'), (1, b'Android'), (2, b'IOS'), (3, b'\xe6\xb5\x8f\xe8\xa7\x88\xe5\x99\xa8')]),
        ),
        migrations.AlterField(
            model_name='mamadevicestats',
            name='renew_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u5988\u5988\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='mamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='potentialmama',
            name='last_renew_type',
            field=models.IntegerField(default=15, verbose_name='\u6700\u540e\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='referalrelationship',
            name='referal_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='teamcarrytotalrecord',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='weekmamacarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='weekmamateamcarrytotal',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='last_renew_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u6700\u8fd1\u7eed\u8d39\u7c7b\u578b', choices=[(3, '\u8bd5\u75283'), (15, '\u8bd5\u752815'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
    ]
