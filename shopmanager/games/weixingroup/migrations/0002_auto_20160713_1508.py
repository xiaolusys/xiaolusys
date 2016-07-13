# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weixingroup', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activity',
            options={'verbose_name': '\u6d3b\u52a8', 'verbose_name_plural': '\u6d3b\u52a8\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='activityusers',
            options={'verbose_name': '\u6d3b\u52a8', 'verbose_name_plural': '\u6d3b\u52a8\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='groupfans',
            options={'verbose_name': '\u5c0f\u9e7f\u5fae\u4fe1\u7fa4\u7c89\u4e1d', 'verbose_name_plural': '\u5c0f\u9e7f\u5fae\u4fe1\u7fa4\u7c89\u4e1d\u8868'},
        ),
        migrations.AlterModelOptions(
            name='groupmamaadministrator',
            options={'verbose_name': '\u5c0f\u9e7f\u5fae\u4fe1\u7fa4\u7ec4', 'verbose_name_plural': '\u5c0f\u9e7f\u5fae\u4fe1\u7fa4\u7ec4\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='xiaoluadministrator',
            options={'verbose_name': '\u5c0f\u9e7f\u5fae\u4fe1\u7fa4\u7ba1\u7406\u5458', 'verbose_name_plural': '\u5c0f\u9e7f\u5fae\u4fe1\u7fa4\u7ba1\u7406\u5458\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='activityusers',
            name='group',
            field=models.ForeignKey(default=None, to='weixingroup.GroupMamaAdministrator'),
            preserve_default=False,
        ),
    ]
