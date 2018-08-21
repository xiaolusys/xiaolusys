# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyerGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('buyer_name', models.CharField(max_length=32, null=True, verbose_name='\u4e70\u624b\u59d3\u540d', blank=True)),
                ('buyer_group', models.IntegerField(default=0, blank=True, verbose_name='\u4e70\u624b\u5206\u7ec4', choices=[(0, '\u672a\u5206\u7ec4'), (1, 'A\u7ec4'), (2, 'B\u7ec4'), (3, 'C\u7ec4')])),
                ('created', models.DateTimeField(auto_now=True, verbose_name='\u521b\u5efa\u65e5\u671f', null=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='\u4fee\u6539\u65e5\u671f', null=True)),
            ],
            options={
                'db_table': 'supply_chain_buyer_group',
                'verbose_name': '\u4e70\u624b\u5206\u7ec4',
                'verbose_name_plural': '\u4e70\u624b\u5206\u7ec4\u5217\u8868',
            },
        ),
    ]
