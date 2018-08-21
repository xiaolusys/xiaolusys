# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('categorys', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, auto_now_add=True, verbose_name='\u521b\u5efa\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='grade',
            field=models.IntegerField(default=0, verbose_name='\u7c7b\u76ee\u7b49\u7ea7', db_index=True),
        ),
        migrations.AddField(
            model_name='category',
            name='modified',
            field=models.DateTimeField(default=django.utils.timezone.now, auto_now=True, verbose_name='\u4fee\u6539\u65e5\u671f', db_index=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='category',
            name='cid',
            field=models.IntegerField(serialize=False, verbose_name='\u7c7b\u76eeID', primary_key=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='is_parent',
            field=models.BooleanField(default=True, verbose_name='\u7236\u7c7b\u76ee'),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=32, verbose_name='\u7c7b\u76ee\u540d', blank=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='parent_cid',
            field=models.IntegerField(null=True, verbose_name='\u7236\u7c7b\u76eeID', db_index=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='sort_order',
            field=models.IntegerField(null=True, verbose_name='\u6743\u503c'),
        ),
        migrations.AlterField(
            model_name='category',
            name='status',
            field=models.CharField(default=b'normal', max_length=7, verbose_name='\u72b6\u6001', choices=[(b'normal', '\u6b63\u5e38'), (b'delete', '\u5220\u9664')]),
        ),
    ]
