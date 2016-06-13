# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0002_create_receiptgoods'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='receiptgoods',
            unique_together=set([('express_no', 'express_company')]),
        ),
    ]
