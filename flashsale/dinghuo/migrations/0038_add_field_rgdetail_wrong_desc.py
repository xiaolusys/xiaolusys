# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dinghuo', '0037_lackgoodorder_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='rgdetail',
            name='wrong_desc',
            field=models.CharField(default=b'', help_text='0\u6216\u5165\u5e93\u5355id', max_length=100, verbose_name='\u9519\u8d27\u63cf\u8ff0'),
        ),
    ]
