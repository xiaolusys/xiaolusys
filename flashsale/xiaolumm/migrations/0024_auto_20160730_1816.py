# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0023_add_cover_image_to_lesson_topic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='awardcarry',
            name='carry_type',
            field=models.IntegerField(default=0, verbose_name='\u5956\u52b1\u7c7b\u578b', choices=[(1, '\u76f4\u8350\u5956\u52b1'), (2, '\u56e2\u961f\u5956\u52b1'), (3, '\u6388\u8bfe\u5956\u91d1'), (4, '\u4efb\u52a1\u5956\u52b1')]),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='contributor_img',
            field=models.CharField(max_length=256, null=True, verbose_name='\u8d21\u732e\u8005\u5934\u50cf', blank=True),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='contributor_mama_id',
            field=models.BigIntegerField(default=0, null=True, verbose_name='\u8d21\u732e\u8005mama_id'),
        ),
        migrations.AlterField(
            model_name='awardcarry',
            name='contributor_nick',
            field=models.CharField(max_length=64, null=True, verbose_name='\u8d21\u732e\u8005\u6635\u79f0', blank=True),
        ),
    ]
