# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0033_mamafortune_history_cashout'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='xlmmmessage',
            options={'verbose_name': '\u5988\u5988\u6d88\u606f/\u901a\u77e5', 'verbose_name_plural': '\u5988\u5988\u6d88\u606f/\u901a\u77e5\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='xlmmmessagerel',
            options={'verbose_name': '\u5988\u5988\u6d88\u606f/\u9605\u8bfb\u72b6\u6001', 'verbose_name_plural': '\u5988\u5988\u6d88\u606f/\u9605\u8bfb\u72b6\u6001\u5217\u8868'},
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u65b0\u624b\u4efb\u52a1'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u63a8\u8350\u65b0\u624b\u4efb\u52a1'), (7, '\u4e00\u5143\u9080\u8bf7')]),
        ),
        migrations.AlterField(
            model_name='ordercarry',
            name='carry_type',
            field=models.IntegerField(default=1, verbose_name='\u63d0\u6210\u7c7b\u578b', choices=[(1, '\u5fae\u5546\u57ce\u8ba2\u5355'), (2, 'App\u8ba2\u5355\u989d\u5916+10%'), (3, '\u4e0b\u5c5e\u8ba2\u5355+20%')]),
        ),
    ]
