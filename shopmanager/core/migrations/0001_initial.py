# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE django_admin_log CHANGE COLUMN object_id object_id varchar(32) DEFAULT NULL;"),
        migrations.RunSQL(
            "ALTER TABLE django_admin_log ADD INDEX IDX_OB_CO_AC(OBJECT_ID, CONTENT_TYPE_ID, ACTION_TIME);"),
        migrations.RunSQL(
            "ALTER TABLE auth_user ADD INDEX IDX_IS_STAFF(is_staff);"),
    ]
