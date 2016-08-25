# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0048_add_cat_type_to_mission'),
    ]

    operations = [
        migrations.CreateModel(
            name='MamaAdministrator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('administrator', models.ForeignKey(to='weixingroup.XiaoluAdministrator')),
                ('mama', models.ForeignKey(to='xiaolumm.XiaoluMama')),
            ],
            options={
                'db_table': 'xiaolumm_mamaadministrator',
                'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u7ba1\u7406\u5458',
                'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u7ba1\u7406\u5458\u5217\u8868',
            },
        ),
    ]
