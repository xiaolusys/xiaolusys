# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0064_add_mama_sale_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='ninepicadver',
            name='save_times',
            field=models.IntegerField(default=0, verbose_name='\u4fdd\u5b58\u6b21\u6570'),
        ),
        migrations.AddField(
            model_name='ninepicadver',
            name='share_times',
            field=models.IntegerField(default=0, verbose_name='\u5206\u4eab\u6b21\u6570'),
        ),
        migrations.AlterField(
            model_name='mamadailytabvisit',
            name='stats_tab',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, 'WX/\u5e97\u94fa\u6fc0\u6d3b'), (15, 'WX/APP\u4e0b\u8f7d'), (16, 'WX/\u5f00\u5e97\u4e8c\u7ef4\u7801'), (17, 'WX/\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801'), (18, 'WX/\u5ba2\u670d\u83dc\u5355'), (19, 'WX/\u4e2a\u4eba\u5e10\u6237'), (20, 'WX/\u63d0\u73b0\u9875APP\u4e0b\u8f7d'), (21, 'WX/\u8df3\u8f6c\u4e13\u9898\u94fe\u63a5'), (22, 'WX/\u8df3\u8f6c\u5fae\u4fe1\u6587\u7ae0'), (23, 'WX/\u65b0\u624b\u6559\u7a0b'), (24, 'WX/\u7ed1\u5b9a\u624b\u673a'), (25, 'WX/\u70b9\u51fb\u6536\u76ca\u63a8\u9001')]),
        ),
        migrations.AlterField(
            model_name='mamatabvisitstats',
            name='stats_tab',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, 'WX/\u5e97\u94fa\u6fc0\u6d3b'), (15, 'WX/APP\u4e0b\u8f7d'), (16, 'WX/\u5f00\u5e97\u4e8c\u7ef4\u7801'), (17, 'WX/\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801'), (18, 'WX/\u5ba2\u670d\u83dc\u5355'), (19, 'WX/\u4e2a\u4eba\u5e10\u6237'), (20, 'WX/\u63d0\u73b0\u9875APP\u4e0b\u8f7d'), (21, 'WX/\u8df3\u8f6c\u4e13\u9898\u94fe\u63a5'), (22, 'WX/\u8df3\u8f6c\u5fae\u4fe1\u6587\u7ae0'), (23, 'WX/\u65b0\u624b\u6559\u7a0b'), (24, 'WX/\u7ed1\u5b9a\u624b\u673a'), (25, 'WX/\u70b9\u51fb\u6536\u76ca\u63a8\u9001')]),
        ),
        migrations.AlterField(
            model_name='weixinpushevent',
            name='event_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u4e8b\u4ef6\u7c7b\u578b', choices=[(1, '\u7c89\u4e1d\u589e\u52a0'), (2, '\u9080\u8bf7\u5956\u52b1\u751f\u6210'), (3, '\u9080\u8bf7\u5956\u52b1\u786e\u5b9a'), (5, '\u5173\u6ce8\u516c\u4f17\u53f7'), (4, '\u8ba2\u5355\u4f63\u91d1\u751f\u6210'), (6, '\u4e0b\u5c5e\u8ba2\u5355\u4f63\u91d1\u751f\u6210'), (7, '\u70b9\u51fb\u6536\u76ca'), (8, '\u62fc\u56e2\u6210\u529f')]),
        ),
    ]
