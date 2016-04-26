# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MonthTradeReportStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('seller_id', models.CharField(max_length=64, blank=True)),
                ('year', models.IntegerField(null=True)),
                ('month', models.IntegerField(null=True)),
                ('update_order', models.BooleanField(default=False)),
                ('update_purchase', models.BooleanField(default=False)),
                ('update_amount', models.BooleanField(default=False)),
                ('update_purchase_amount', models.BooleanField(default=False)),
                ('update_logistics', models.BooleanField(default=False)),
                ('update_refund', models.BooleanField(default=False)),
                ('order_task_id', models.CharField(max_length=128, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'shop_report_monthreportstatus',
            },
        ),
        migrations.AlterUniqueTogether(
            name='monthtradereportstatus',
            unique_together=set([('seller_id', 'year', 'month')]),
        ),
    ]
