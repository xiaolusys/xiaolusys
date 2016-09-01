# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0005_create_table_shop_weixin_template_msg'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='weixinfans',
            options={'verbose_name': '\u5fae\u4fe1\u516c\u4f17\u53f7\u7c89\u4e1d', 'verbose_name_plural': '\u5fae\u4fe1\u516c\u4f17\u53f7\u7c89\u4e1d\u5217\u8868'},
        ),
        migrations.AlterModelOptions(
            name='weixintplmsg',
            options={'verbose_name': '\u5fae\u4fe1\u6a21\u677f\u6d88\u606f', 'verbose_name_plural': '\u5fae\u4fe1\u6a21\u677f\u6d88\u606f\u5217\u8868'},
        ),
        migrations.AddField(
            model_name='weixinfans',
            name='extras',
            field=jsonfield.fields.JSONField(default={b'qrscene': 0}, max_length=512, verbose_name='\u989d\u5916\u53c2\u6570'),
        ),
    ]
