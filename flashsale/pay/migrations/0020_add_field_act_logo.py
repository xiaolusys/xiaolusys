# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0019_add_model_activity_product'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityentry',
            name='act_logo',
            field=models.CharField(max_length=256, verbose_name='\u54c1\u724cLOGO', blank=True),
        ),
        migrations.AlterField(
            model_name='activityentry',
            name='act_type',
            field=models.CharField(db_index=True, max_length=8, verbose_name='\u6d3b\u52a8\u7c7b\u578b', choices=[(b'webview', '\u666e\u901a\u6d3b\u52a8'), (b'atop', '\u5546\u57ceTop10'), (b'topic', '\u4e13\u9898\u6d3b\u52a8'), (b'brand', '\u54c1\u724c\u4e13\u573a'), (b'coupon', '\u4f18\u60e0\u5238\u6d3b\u52a8'), (b'mama', '\u5988\u5988\u6d3b\u52a8')]),
        ),
        migrations.AlterField(
            model_name='activityentry',
            name='title',
            field=models.CharField(db_index=True, max_length=32, verbose_name='\u6d3b\u52a8/\u54c1\u724c\u540d\u79f0', blank=True),
        ),
        migrations.AlterField(
            model_name='activityproduct',
            name='activity',
            field=models.ForeignKey(related_name='activity_products', verbose_name='\u6240\u5c5e\u4e13\u9898', to='pay.ActivityEntry'),
        ),
    ]
