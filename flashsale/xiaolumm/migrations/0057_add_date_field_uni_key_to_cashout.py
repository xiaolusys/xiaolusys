# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0056_mamamission_desc'),
    ]

    operations = [
        migrations.AddField(
            model_name='cashout',
            name='date_field',
            field=models.DateField(default=datetime.date.today, verbose_name='\u65e5\u671f', db_index=True),
        ),
        migrations.AddField(
            model_name='cashout',
            name='uni_key',
            field=models.CharField(max_length=128, unique=True, null=True, verbose_name='\u552f\u4e00ID', blank=True),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u63a8\u8350\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u65b0\u624b\u4efb\u52a1'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u63a8\u8350\u65b0\u624b\u4efb\u52a1'), (7, '\u4e00\u5143\u9080\u8bf7'), (8, '\u5173\u6ce8\u516c\u4f17\u53f7'), (9, '\u9500\u552e\u5956\u52b1'), (10, '\u56e2\u961f\u9500\u552e\u5956\u52b1'), (11, '\u7c89\u4e1d\u9080\u8bf7')]),
        ),
        migrations.AlterField(
            model_name='envelop',
            name='subject',
            field=models.CharField(db_index=True, max_length=8, verbose_name='\u7ea2\u5305\u4e3b\u9898', choices=[(b'cashout', '\u5988\u5988\u4f59\u989d\u63d0\u73b0'), (b'ordred', '\u8ba2\u5355\u7ea2\u5305'), (b'xlapp', '\u4e2a\u4eba\u96f6\u94b1\u63d0\u73b0')]),
        ),
        migrations.AlterField(
            model_name='mamadailytabvisit',
            name='stats_tab',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, '\u5e97\u94fa\u6fc0\u6d3b')]),
        ),
        migrations.AlterField(
            model_name='mamamission',
            name='cat_type',
            field=models.CharField(default=b'sale_mama', max_length=16, verbose_name='\u4efb\u52a1\u7c7b\u578b', db_index=True, choices=[(b'sale_mama', '\u4e2a\u4eba\u9500\u552e'), (b'sale_group', '\u56e2\u961f\u9500\u552e'), (b'refer_mama', '\u65b0\u589e\u4e0b\u5c5e\u5988\u5988'), (b'group_refer', '\u65b0\u589e\u56e2\u961f\u5988\u5988'), (b'first_order', '\u9996\u5355\u5956\u52b1'), (b'open_course', '\u6388\u8bfe\u5956\u91d1'), (b'join_guide', '\u65b0\u624b\u4efb\u52a1'), (b'trial_mama', '\u9080\u8bf7\u5988\u5988\u8bd5\u7528\u5f00\u5e97'), (b'refer_guide', '\u65b0\u624b\u6307\u5bfc')]),
        ),
        migrations.AlterField(
            model_name='mamatabvisitstats',
            name='stats_tab',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, '\u5e97\u94fa\u6fc0\u6d3b')]),
        ),
        migrations.AlterField(
            model_name='ordercarry',
            name='order_id',
            field=models.CharField(db_index=True, max_length=64, verbose_name='\u8ba2\u5355ID', blank=True),
        ),
    ]
