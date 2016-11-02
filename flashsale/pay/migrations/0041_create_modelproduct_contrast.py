# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pay', '0040_teambuy_detail_add_created'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelProductSkuContrast',
            fields=[
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True)),
                ('modelproduct', models.OneToOneField(related_name='contrast', primary_key=True, serialize=False, to='pay.ModelProduct', verbose_name='\u6b3e\u5f0fID')),
                ('contrast_detail', jsonfield.fields.JSONField(default=dict, max_length=10240, verbose_name='\u5bf9\u7167\u8be6\u60c5', blank=True)),
            ],
            options={
                'db_table': 'pay_modelproduct_contrast',
                'verbose_name': '\u7279\u5356\u5546\u54c1/\u6b3e\u5f0f\u5c3a\u7801\u5bf9\u7167\u8868',
                'verbose_name_plural': '\u7279\u5356\u5546\u54c1/\u6b3e\u5f0f\u5c3a\u7801\u5bf9\u7167\u5217\u8868',
            },
        )
    ]
