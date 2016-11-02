# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0016_alter_nic_array_and_lesson_type'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clickplan',
            options={'ordering': ['-created'], 'verbose_name': 'V2/\u70b9\u51fb\u8ba1\u5212', 'verbose_name_plural': 'V2/\u70b9\u51fb\u8ba1\u5212\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='agencyorderrebetascheme',
            name='end_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True),
        ),
        migrations.AddField(
            model_name='agencyorderrebetascheme',
            name='start_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u751f\u6548\u65f6\u95f4', blank=True),
        ),
        migrations.AddField(
            model_name='clickplan',
            name='default',
            field=models.BooleanField(default=False, verbose_name='\u7f3a\u7701\u8bbe\u7f6e'),
        ),
        migrations.AddField(
            model_name='clickplan',
            name='end_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', blank=True),
        ),
        migrations.AddField(
            model_name='clickplan',
            name='start_time',
            field=models.DateTimeField(db_index=True, null=True, verbose_name='\u751f\u6548\u65f6\u95f4', blank=True),
        ),
        migrations.AlterField(
            model_name='lessontopic',
            name='lesson_type',
            field=models.IntegerField(default=0, verbose_name='\u7c7b\u578b', choices=[(3, '\u57fa\u7840\u8bfe\u7a0b'), (0, '\u8bfe\u7a0b'), (1, '\u5b9e\u6218'), (2, '\u77e5\u8bc6')]),
        ),
    ]
