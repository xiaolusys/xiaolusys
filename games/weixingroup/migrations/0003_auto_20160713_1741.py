# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0002_auto_20160713_1508'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityusers',
            name='activity',
            field=models.ForeignKey(to='pay.ActivityEntry'),
        ),
        migrations.AlterField(
            model_name='groupmamaadministrator',
            name='status',
            field=models.IntegerField(default=1, verbose_name='\u72b6\u6001', choices=[(1, '\u6709\u6548'), (2, '\u4f5c\u5e9f')]),
        ),
        migrations.AlterUniqueTogether(
            name='groupmamaadministrator',
            unique_together=set([('mama_id', 'status')]),
        ),
        migrations.DeleteModel(
            name='Activity',
        ),
    ]
