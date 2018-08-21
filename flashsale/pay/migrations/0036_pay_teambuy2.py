# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0035_pay_teambuy'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='teambuydetail',
            name='status',
        ),
        migrations.AddField(
            model_name='teambuy',
            name='limit_person_num',
            field=models.IntegerField(default=3, verbose_name='\u6210\u56e2\u4eba\u6570'),
        ),
        migrations.AlterField(
            model_name='teambuy',
            name='limit_time',
            field=models.DateTimeField(verbose_name='\u6700\u8fdf\u6210\u56e2\u65f6\u95f4', db_index=True),
        ),
        migrations.AlterField(
            model_name='teambuydetail',
            name='originizer',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='teambuydetail',
            name='teambuy',
            field=models.ForeignKey(related_name='details', to='pay.TeamBuy'),
        ),
    ]
