# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0007_change_head_img_len'),
    ]

    operations = [
        migrations.AddField(
            model_name='activityusers',
            name='gifted',
            field=models.IntegerField(help_text='1\u51c9\u5e2d', null=True, verbose_name='\u83b7\u53d6\u8d60\u54c1'),
        ),
        migrations.AddField(
            model_name='groupfans',
            name='gifted',
            field=models.IntegerField(help_text='1\u51c9\u5e2d', null=True, verbose_name='\u83b7\u53d6\u8d60\u54c1'),
        )
    ]
