# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0004_change_inbound_verbose_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inbounddetail',
            name='product',
            field=models.ForeignKey(related_name='inbound_details', verbose_name='\u5165\u5e93\u5546\u54c1', blank=True, to='items.Product', null=True),
        ),
    ]
