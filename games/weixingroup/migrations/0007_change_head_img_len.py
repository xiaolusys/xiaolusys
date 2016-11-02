# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0006_auto_20160714_1523'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupfans',
            name='head_img_url',
            field=models.CharField(max_length=256, verbose_name='\u7528\u6237\u5fae\u4fe1\u5934\u50cf'),
        )
    ]
