# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models
import jsonfield.fields
import flashsale.xiaolumm.models.models_fortune


class Migration(migrations.Migration):
    dependencies = [
        ('xiaolumm', '0005_auto_20160507_1544'),
    ]
    operations = [
        migrations.AddField(
            model_name='mamafortune',
            name='extras',
            field=jsonfield.fields.JSONField(default=flashsale.xiaolumm.models.models_fortune.default_mama_extras, max_length=1024, null=True, verbose_name='\u9644\u52a0\u4fe1\u606f', blank=True),
        ),
    ]
