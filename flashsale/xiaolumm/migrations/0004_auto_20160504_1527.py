# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0003_auto_20160503_0020'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructor',
            name='mama_id',
            field=models.IntegerField(default=0, verbose_name='Mama ID', db_index=True),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1')]),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='status',
            field=models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='lesson',
            name='status',
            field=models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u5df2\u5b8c\u6210'), (3, '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='lessonattendrecord',
            name='status',
            field=models.IntegerField(default=2, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u65e0\u6548')]),
        ),
        migrations.AlterField(
            model_name='lessontopic',
            name='status',
            field=models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='topicattendrecord',
            name='status',
            field=models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(1, 'EFFECT'), (2, 'CANCELED')]),
        ),
        migrations.AlterField(
            model_name='topicattendrecord',
            name='student_image',
            field=models.CharField(max_length=256, verbose_name='\u5b66\u5458\u5934\u50cf', blank=True),
        ),
        migrations.AlterField(
            model_name='topicattendrecord',
            name='student_nick',
            field=models.CharField(max_length=64, verbose_name='\u5b66\u5458\u6635\u79f0', blank=True),
        ),
    ]
