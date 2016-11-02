# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields
import flashsale.mmexam.models


class Migration(migrations.Migration):

    dependencies = [
        ('mmexam', '0003_alter_field_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mamaexam',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('sheaves', models.IntegerField(verbose_name='\u8003\u8bd5\u8f6e\u6570', db_index=True)),
                ('start_time', models.DateTimeField(null=True, verbose_name='\u5f00\u653e\u65f6\u95f4', db_index=True)),
                ('expire_time', models.DateTimeField(null=True, verbose_name='\u7ed3\u675f\u65f6\u95f4', db_index=True)),
                ('valid', models.BooleanField(default=False, db_index=True, verbose_name='\u662f\u5426\u6709\u6548')),
                ('extras', jsonfield.fields.JSONField(default=flashsale.mmexam.models.default_mamaexam_extras, max_length=512, null=True, verbose_name='\u9644\u52a0\u4fe1\u606f', blank=True)),
            ],
            options={
                'db_table': 'flashsale_mmexam_sheaves',
                'verbose_name': '\u4ee3\u7406\u8003\u8bd5\u8f6e\u6570',
                'verbose_name_plural': '\u4ee3\u7406\u8003\u8bd5\u9898\u76ee\u8f6e\u6570\u5217\u8868',
            },
        ),
    ]
