# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('complain', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='complain',
            options={'ordering': ('created_time', 'user_id'), 'verbose_name': '\u95ee\u9898\u53cd\u9988', 'verbose_name_plural': '\u6295\u8bc9\u5efa\u8bae\u8868'},
        ),
        migrations.RenameField(
            model_name='complain',
            old_name='insider_phone',
            new_name='user_id',
        ),
        migrations.AlterField(
            model_name='complain',
            name='status',
            field=models.IntegerField(default=0, verbose_name='\u72b6\u6001', choices=[(0, '\u672a\u5904\u7406'), (1, '\u5df2\u56de\u590d'), (2, '\u5df2\u5173\u95ed'), (3, '\u5df2\u5220\u9664')]),
        ),
    ]
