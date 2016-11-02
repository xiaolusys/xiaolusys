# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xiaolumm', '0029_mama_fortune_add_invite_num'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='xlmmmessagerel',
            unique_together=set([('mama', 'message')]),
        ),
    ]
