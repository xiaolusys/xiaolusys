# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weixinunionid',
            name='unionid',
            field=models.CharField(max_length=32, verbose_name='UNIONID'),
        ),
        migrations.AlterUniqueTogether(
            name='weixinunionid',
            unique_together=set([('unionid', 'app_key')]),
        ),
        migrations.AlterIndexTogether(
            name='weixinunionid',
            index_together=set([('openid', 'app_key')]),
        ),
    ]
