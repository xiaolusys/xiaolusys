# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-18 10:49
from __future__ import unicode_literals

from django.db import migrations
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('weixin', '0009_add_template_ids'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weixintplmsg',
            name='template_ids',
            field=jsonfield.fields.JSONField(blank=True, default={}, max_length=512, verbose_name='\u6a21\u7248ID\u96c6\u5408'),
        ),
    ]
