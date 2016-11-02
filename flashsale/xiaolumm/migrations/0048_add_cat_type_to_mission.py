# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0047_unique_potential_mama'),
    ]

    operations = [
        migrations.AddField(
            model_name='mamamission',
            name='cat_type',
            field=models.CharField(default=b'sale_mama', max_length=16, verbose_name='\u4efb\u52a1\u7c7b\u578b', db_index=True, choices=[(b'sale_mama', '\u4e2a\u4eba\u9500\u552e'), (b'sale_group', '\u56e2\u961f\u9500\u552e'), (b'refer_mama', '\u65b0\u589e\u4e0b\u5c5e\u5988\u5988'), (b'group_refer', '\u65b0\u589e\u56e2\u961f\u5988\u5988'), (b'first_order', '\u9996\u5355\u5956\u52b1'), (b'open_course', '\u6388\u8bfe\u5956\u91d1'), (b'join_guide', '\u65b0\u624b\u4efb\u52a1'), (b'trial_mama', '\u65b0\u589e1\u5143\u5988\u5988'), (b'refer_guide', '\u65b0\u624b\u6307\u5bfc')]),
        ),
        migrations.AlterField(
            model_name='grouprelationship',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u65e0\u6548')]),
        ),
        migrations.AlterField(
            model_name='mamamission',
            name='date_type',
            field=models.CharField(default=b'weekly', max_length=8, verbose_name='\u4efb\u52a1\u5468\u671f', choices=[(b'weekly', '\u5468\u4efb\u52a1'), (b'monthly', '\u6708\u4efb\u52a1'), (b'oncetime', '\u4e00\u6b21\u6027\u4efb\u52a1'), (b'deadline', 'DEADLINE')]),
        ),
        migrations.AlterField(
            model_name='referalrelationship',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u65e0\u6548')]),
        ),
    ]
