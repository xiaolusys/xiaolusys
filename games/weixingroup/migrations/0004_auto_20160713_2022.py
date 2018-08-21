# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0003_auto_20160713_1741'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activityusers',
            options={'verbose_name': '\u53c2\u4e0e\u7528\u6237', 'verbose_name_plural': '\u53c2\u4e0e\u7528\u6237\u5217\u8868'},
        ),
        migrations.AlterField(
            model_name='groupfans',
            name='group',
            field=models.ForeignKey(related_name='fans', to='weixingroup.GroupMamaAdministrator'),
        ),
        migrations.AlterField(
            model_name='xiaoluadministrator',
            name='username',
            field=models.CharField(max_length=64, verbose_name='\u7ba1\u7406\u5458\u7528\u6237\u540d'),
        ),
    ]
