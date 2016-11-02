# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0034_inbound_inferior'),
    ]

    operations = [
        migrations.AddField(
            model_name='inbound',
            name='return_goods',
            field=models.ForeignKey(verbose_name='\u9000\u8d27\u5355', blank=True, to='dinghuo.ReturnGoods', null=True),
        )
    ]
