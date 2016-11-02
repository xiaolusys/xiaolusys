# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductPageRank',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('keyword', models.CharField(max_length=20, db_index=True)),
                ('item_id', models.CharField(max_length=32, db_index=True)),
                ('title', models.CharField(max_length=60)),
                ('user_id', models.CharField(max_length=32)),
                ('nick', models.CharField(max_length=20, db_index=True)),
                ('month', models.IntegerField(null=True, db_index=True)),
                ('day', models.IntegerField(null=True, db_index=True)),
                ('time', models.CharField(max_length=5, db_index=True)),
                ('created', models.CharField(db_index=True, max_length=19, blank=True)),
                ('rank', models.IntegerField()),
            ],
            options={
                'db_table': 'shop_collector_pagerank',
            },
        ),
        migrations.CreateModel(
            name='ProductTrade',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('item_id', models.CharField(max_length=32, db_index=True)),
                ('user_id', models.CharField(max_length=32, db_index=True)),
                ('nick', models.CharField(max_length=20, db_index=True)),
                ('trade_id', models.CharField(max_length=20, db_index=True)),
                ('num', models.IntegerField(null=True)),
                ('price', models.CharField(max_length=10, blank=True)),
                ('trade_at', models.CharField(db_index=True, max_length=19, blank=True)),
                ('state', models.CharField(max_length=12, blank=True)),
                ('year', models.IntegerField(null=True, db_index=True)),
                ('month', models.IntegerField(null=True, db_index=True)),
                ('week', models.IntegerField(null=True, db_index=True)),
                ('day', models.IntegerField(null=True, db_index=True)),
                ('hour', models.IntegerField(null=True, db_index=True)),
            ],
            options={
                'db_table': 'shop_collector_producttrade',
            },
        ),
    ]
