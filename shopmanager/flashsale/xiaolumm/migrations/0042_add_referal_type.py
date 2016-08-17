# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0041_mamadailytabvisit_mamadevicestats_mamatabvisitstats'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mamadevicestats',
            options={'verbose_name': 'V2/\u5988\u5988device\u7edf\u8ba1', 'verbose_name_plural': 'V2/\u5988\u5988device\u7edf\u8ba1\u8868'},
        ),
        migrations.AlterModelOptions(
            name='weekmamacarrytotal',
            options={'verbose_name': '\u5c0f\u9e7f\u5988\u5988\u56e2\u961f\u6536\u76ca\u5468\u6392\u540d', 'verbose_name_plural': '\u5c0f\u9e7f\u5988\u5988\u56e2\u961f\u6536\u76ca\u5468\u6392\u540d\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='grouprelationship',
            name='referal_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='grouprelationship',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, b'Valid'), (2, b'Invalid')]),
        ),
        migrations.AddField(
            model_name='referalrelationship',
            name='order_id',
            field=models.CharField(max_length=64, verbose_name='\u8ba2\u5355ID', blank=True),
        ),
        migrations.AddField(
            model_name='referalrelationship',
            name='referal_type',
            field=models.IntegerField(default=365, db_index=True, verbose_name='\u7c7b\u578b', choices=[(15, '\u8bd5\u7528'), (183, '\u534a\u5e74'), (365, '\u4e00\u5e74')]),
        ),
        migrations.AddField(
            model_name='referalrelationship',
            name='status',
            field=models.IntegerField(default=1, db_index=True, verbose_name='\u72b6\u6001', choices=[(1, b'Valid'), (2, b'Invalid')]),
        ),
    ]
