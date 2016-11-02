# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0063_add_category_ninepic_models'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaSaleGrade',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('grade', models.IntegerField(default=0, db_index=True, verbose_name='\u9500\u552e\u7ea7\u522b', choices=[(30000, 'A\u7ea7: <300\u5143'), (60000, 'B\u7ea7: <600\u5143'), (90000, 'C\u7ea7: <900\u5143'), (120000, 'D\u7ea7: <1200\u5143'), (150000, 'E\u7ea7: <1500\u5143'), (180000, 'F\u7ea7: <1800\u5143'), (210000, 'G\u7ea7: <2100\u5143')])),
                ('combo_count', models.IntegerField(default=0, verbose_name='\u8fde\u51fb\u6b21\u6570', db_index=True)),
                ('last_record_time', models.DateTimeField(null=True, verbose_name='\u6700\u540e\u4efb\u52a1\u8bb0\u5f55\u65f6\u95f4', blank=True)),
                ('total_finish_count', models.IntegerField(default=0, verbose_name='\u7d2f\u8ba1\u5b8c\u6210\u6b21\u6570')),
                ('first_finish_time', models.DateTimeField(db_index=True, null=True, verbose_name='\u6700\u65e9\u5b8c\u6210\u65f6\u95f4', blank=True)),
            ],
            options={
                'db_table': 'flashsale_xlmm_salegrade',
                'verbose_name': 'V2/\u5988\u5988\u9500\u552e\u4e1a\u7ee9',
                'verbose_name_plural': 'V2/\u5988\u5988\u9500\u552e\u4e1a\u7ee9\u5217\u8868',
            },
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u63a8\u8350\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u65b0\u624b\u4efb\u52a1'), (5, '\u9996\u5355\u5956\u52b1'), (6, '\u63a8\u8350\u65b0\u624b\u4efb\u52a1'), (7, '\u4e00\u5143\u9080\u8bf7'), (8, '\u5173\u6ce8\u516c\u4f17\u53f7'), (9, '\u9500\u552e\u5956\u52b1'), (10, '\u56e2\u961f\u9500\u552e\u5956\u52b1'), (11, '\u7c89\u4e1d\u9080\u8bf7')]),
        ),
        migrations.AlterField(
            model_name='mamadailytabvisit',
            name='stats_tab',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, 'WX/\u5e97\u94fa\u6fc0\u6d3b'), (15, 'WX/APP\u4e0b\u8f7d'), (16, 'WX/\u5f00\u5e97\u4e8c\u7ef4\u7801'), (17, 'WX/\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801'), (18, 'WX/\u5ba2\u670d\u83dc\u5355'), (19, 'WX/\u4e2a\u4eba\u5e10\u6237'), (20, 'WX/\u63d0\u73b0\u9875APP\u4e0b\u8f7d'), (21, 'WX/\u8df3\u8f6c\u4e13\u9898\u94fe\u63a5'), (22, 'WX/\u8df3\u8f6c\u5fae\u4fe1\u6587\u7ae0'), (23, 'WX/\u65b0\u624b\u6559\u7a0b'), (24, 'WX/\u7ed1\u5b9a\u624b\u673a')]),
        ),
        migrations.AlterField(
            model_name='mamatabvisitstats',
            name='stats_tab',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u529f\u80fdTAB', choices=[(0, b'Unknown'), (1, '\u5988\u5988\u4e3b\u9875'), (2, '\u6bcf\u65e5\u63a8\u9001'), (3, '\u6d88\u606f\u901a\u77e5'), (4, '\u5e97\u94fa\u7cbe\u9009'), (5, '\u9080\u8bf7\u5988\u5988'), (6, '\u9009\u54c1\u4f63\u91d1'), (7, 'VIP\u8003\u8bd5'), (8, '\u5988\u5988\u56e2\u961f'), (9, '\u6536\u76ca\u6392\u540d'), (10, '\u8ba2\u5355\u8bb0\u5f55'), (11, '\u6536\u76ca\u8bb0\u5f55'), (12, '\u7c89\u4e1d\u5217\u8868'), (13, '\u8bbf\u5ba2\u5217\u8868'), (14, 'WX/\u5e97\u94fa\u6fc0\u6d3b'), (15, 'WX/APP\u4e0b\u8f7d'), (16, 'WX/\u5f00\u5e97\u4e8c\u7ef4\u7801'), (17, 'WX/\u7ba1\u7406\u5458\u4e8c\u7ef4\u7801'), (18, 'WX/\u5ba2\u670d\u83dc\u5355'), (19, 'WX/\u4e2a\u4eba\u5e10\u6237'), (20, 'WX/\u63d0\u73b0\u9875APP\u4e0b\u8f7d'), (21, 'WX/\u8df3\u8f6c\u4e13\u9898\u94fe\u63a5'), (22, 'WX/\u8df3\u8f6c\u5fae\u4fe1\u6587\u7ae0'), (23, 'WX/\u65b0\u624b\u6559\u7a0b'), (24, 'WX/\u7ed1\u5b9a\u624b\u673a')]),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='created',
            field=models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
        ),
        migrations.AlterField(
            model_name='xiaolumama',
            name='modified',
            field=models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
        ),
        migrations.AddField(
            model_name='mamasalegrade',
            name='mama',
            field=models.OneToOneField(related_name='sale_grade', verbose_name='\u5173\u8054\u5988\u5988', to='xiaolumm.XiaoluMama'),
        ),
    ]
