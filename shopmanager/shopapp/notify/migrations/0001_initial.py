# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ItemNotify',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('user_id', models.BigIntegerField()),
                ('num_iid', models.BigIntegerField()),
                ('title', models.CharField(max_length=64, blank=True)),
                ('sku_id', models.BigIntegerField(null=True, blank=True)),
                ('sku_num', models.IntegerField(default=0, null=True)),
                ('status', models.CharField(max_length=32, blank=True)),
                ('increment', models.IntegerField(default=0, null=True)),
                ('nick', models.CharField(max_length=32, blank=True)),
                ('num', models.IntegerField(default=0, null=True)),
                ('changed_fields', models.CharField(max_length=256, blank=True)),
                ('price', models.CharField(max_length=10, blank=True)),
                ('modified', models.DateTimeField(db_index=True, null=True, verbose_name='\u4fee\u6539\u65f6\u95f4', blank=True)),
                ('is_exec', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'shop_notify_item',
            },
        ),
        migrations.CreateModel(
            name='RefundNotify',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('user_id', models.BigIntegerField()),
                ('tid', models.BigIntegerField()),
                ('oid', models.BigIntegerField()),
                ('rid', models.BigIntegerField()),
                ('nick', models.CharField(max_length=64, blank=True)),
                ('seller_nick', models.CharField(max_length=64, blank=True)),
                ('buyer_nick', models.CharField(max_length=64, blank=True)),
                ('refund_fee', models.CharField(max_length=10, blank=True)),
                ('status', models.CharField(max_length=32, blank=True)),
                ('modified', models.DateTimeField(db_index=True, null=True, verbose_name='\u4fee\u6539\u65f6\u95f4', blank=True)),
                ('is_exec', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'shop_notify_refund',
            },
        ),
        migrations.CreateModel(
            name='TradeNotify',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True)),
                ('user_id', models.BigIntegerField()),
                ('tid', models.BigIntegerField()),
                ('oid', models.BigIntegerField()),
                ('nick', models.CharField(max_length=64, blank=True)),
                ('seller_nick', models.CharField(max_length=64, blank=True)),
                ('buyer_nick', models.CharField(max_length=64, blank=True)),
                ('payment', models.CharField(max_length=10, blank=True)),
                ('type', models.CharField(max_length=32, blank=True)),
                ('status', models.CharField(max_length=32, blank=True)),
                ('trade_mark', models.CharField(max_length=256, blank=True)),
                ('modified', models.DateTimeField(db_index=True, null=True, verbose_name='\u4fee\u6539\u65f6\u95f4', blank=True)),
                ('is_exec', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'shop_notify_trade',
            },
        ),
        migrations.AlterUniqueTogether(
            name='tradenotify',
            unique_together=set([('user_id', 'tid', 'oid', 'status')]),
        ),
        migrations.AlterUniqueTogether(
            name='refundnotify',
            unique_together=set([('user_id', 'tid', 'oid', 'rid', 'status')]),
        ),
        migrations.AlterUniqueTogether(
            name='itemnotify',
            unique_together=set([('user_id', 'num_iid', 'sku_id', 'status')]),
        ),
    ]
