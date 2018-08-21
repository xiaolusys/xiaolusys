# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mmexam', '0002_change_exam_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='choice',
            name='question',
            field=models.ForeignKey(related_name='question_choices', to='mmexam.Question'),
        ),
        migrations.AlterField(
            model_name='question',
            name='start_time',
            field=models.DateTimeField(null=True, verbose_name='\u8003\u8bd5\u5f00\u59cb\u65e5\u671f', db_index=True),
        ),
        migrations.AlterField(
            model_name='result',
            name='daili_user',
            field=models.CharField(max_length=32, verbose_name='\u4ee3\u7406unionid'),
        ),
        migrations.AlterUniqueTogether(
            name='result',
            unique_together=set([('customer_id', 'sheaves')]),
        ),
    ]
