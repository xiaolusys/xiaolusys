# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', 'add_extras_field_for_mamafortune'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructor',
            name='mama_id',
            field=models.IntegerField(default=0, unique=True, verbose_name='Mama ID'),
        ),
        migrations.AlterField(
            model_name='instructor',
            name='status',
            field=models.IntegerField(default=2, verbose_name='\u72b6\u6001', choices=[(1, '\u5ba1\u6838\u5408\u683c'), (2, '\u5f85\u5ba1\u6838'), (3, '\u53d6\u6d88')]),
        ),
        migrations.AlterField(
            model_name='ordercarry',
            name='carry_type',
            field=models.IntegerField(default=1, verbose_name='\u63d0\u6210\u7c7b\u578b', choices=[(1, 'Web\u76f4\u63a5\u8ba2\u5355'), (2, 'App\u8ba2\u5355\u989d\u5916+10%'), (3, '\u4e0b\u5c5e\u8ba2\u5355+20%')]),
        ),
    ]
