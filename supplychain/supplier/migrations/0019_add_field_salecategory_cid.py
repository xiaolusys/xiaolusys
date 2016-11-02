# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplier', '0018_add_salecategory_created_and_modified'),
    ]

    operations = [
        migrations.AddField(
            model_name='salecategory',
            name='cid',
            field=models.IntegerField(default=0, verbose_name='\u7c7b\u76eeID', db_index=True),
        ),
        migrations.AlterField(
            model_name='salecategory',
            name='grade',
            field=models.IntegerField(default=0, db_index=True, verbose_name='\u7c7b\u76ee\u7b49\u7ea7', choices=[(1, '\u4e00\u7ea7'), (2, '\u4e8c\u7ea7'), (3, '\u4e09\u7ea7'), (4, '\u56db\u7ea7')]),
        ),
    ]
